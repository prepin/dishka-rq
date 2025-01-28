from collections.abc import Callable
from functools import update_wrapper
from inspect import signature
from typing import Any, Final, ParamSpec, TypeVar, get_type_hints

from dishka import Container
from dishka.exceptions import DishkaError
from dishka.integrations.base import default_parse_dependency, wrap_injection
from rq import Queue, Worker, get_current_job
from rq.job import Job


class DishkaWorker(Worker):
    """Custom RQ Worker class with Dishka DI support."""

    def __init__(
        self,
        *args,
        container: Container,
        **kwargs,
    ) -> None:
        """Sets up class and container."""
        super().__init__(*args, **kwargs)
        self.dishka_container = container

    def perform_job(self, job: Job, queue: Queue) -> bool:
        """Performs job call"""
        request_container = self.dishka_container().__enter__()
        self.inject_deps(job, request_container)
        job_result = super().perform_job(job, queue)
        request_container.close()
        return job_result

    def inject_deps(self, job: Job, container: Container) -> None:
        """Injects dependencies into using the Dishka container.

        Args:
            job: The RQ job to inject dependencies into.
        """
        if job.func:
            dependencies = self._build_dependencies(job.func)
            updated_kwargs = self._build_kwargs(dependencies, container)
            if isinstance(job.kwargs, dict):
                job.kwargs.update(updated_kwargs)

    def teardown(self) -> None:
        """Closes DI container on worker shutdown."""
        self.dishka_container.close()
        super().teardown()

    @classmethod
    def _build_dependencies(
        cls,
        callable_: Callable[..., Any],
    ) -> dict[str, Any]:
        """Builds dependencies for the given callable."""
        dependencies = {}

        for name, parameter in signature(callable_).parameters.items():
            dep = default_parse_dependency(
                parameter,
                get_type_hints(callable_, include_extras=True).get(name, Any),
            )
            if dep is None:
                continue
            dependencies[name] = dep

        return dependencies

    def _build_kwargs(
        self,
        dependencies: dict[str, Any],
        request_container: Container,
    ) -> dict[str, Any]:
        """Buld kwargs dict for RQ job run."""
        return {
            name: request_container.get(dep.type_hint, component=dep.component)
            for name, dep in dependencies.items()
        }


T = TypeVar("T")
P = ParamSpec("P")
DISHKA_APP_CONTAINER_KEY: Final = "dishka_app_container"
DISHKA_REQUEST_CONTAINER_KEY: Final = "dishka_request_container"


def _container_getter(args, kwargs) -> Container:
    job = get_current_job()
    if not job:  # pragma: no coverage
        raise
    container = getattr(job, "_dishka_request_container", None)
    if not container:
        raise DishkaError("No container attached to Job.")
    return container


def inject(func: Callable[P, T]) -> Callable[P, T]:
    wrapped = wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=_container_getter,
        is_async=False,
    )
    update_wrapper(wrapped, func)
    return wrapped


def setup_dishka(worker: Worker, container: Container):
    worker_klass = worker.__class__

    old_perform_job = worker_klass.perform_job
    old_teardown = worker_klass.teardown

    def dishka_patched_perform_job(job: Job, queue: Queue) -> bool:
        """Performs job call"""
        request_container = container().__enter__()
        setattr(job, "_dishka_request_container", request_container)
        job_result = old_perform_job(worker, job, queue)
        request_container.close()
        return job_result

    def dishka_patched_teardown():
        """Closes DI container on worker shutdown."""
        container.close()
        old_teardown(worker)

    worker.perform_job = dishka_patched_perform_job
    worker.teardown = dishka_patched_teardown
