from typing import cast
from unittest.mock import Mock

import pytest
from dishka import Container
from dishka.exceptions import DishkaError
from fakeredis import FakeStrictRedis
from rq import Queue, SimpleWorker, Worker
from rq.job import Job

from dishka_rq.rq_integration import setup_dishka

from .common import AppProvider
from .tasks import app_job, just_a_task, non_injected_job, request_job

# Supress CLIENT SETNAME warning from Worker. FakeRedis does not support it.
pytestmark = pytest.mark.filterwarnings("ignore:CLIENT SETNAME")


@pytest.fixture
def redis():
    redis = FakeStrictRedis()
    yield redis
    redis.flushdb


@pytest.fixture
def queue(redis):
    return Queue(name="test_queue", connection=redis)


@pytest.fixture
def worker(queue: Queue, container: Container):
    worker = SimpleWorker([queue], connection=queue.connection)
    setup_dishka(worker, container)
    return worker


def test_inject_app_deps(
    worker: Worker, queue: Queue, app_provider: AppProvider, container
):
    """Should inject app dependencies into task with decorator."""
    job = queue.enqueue(app_job)

    worker.work(burst=True)

    assert job.return_value(refresh=True) == "App Job Done"
    cast(Mock, app_provider.app_mock).assert_called_once()


def test_inject_request_deps(worker: Worker, queue: Queue, app_provider: AppProvider):
    """Should inject request dependencies into task with decorator."""
    job = queue.enqueue(request_job)

    worker.work(burst=True)

    assert job.return_value(refresh=True) == "Request Job Done"
    cast(Mock, app_provider.mock).assert_called_once()


def test_no_inject_decorator(worker: Worker, queue: Queue, app_provider: AppProvider):
    """Should not inject dependencies into task without decorator."""
    worker.disable_default_exception_handler = True
    job = queue.enqueue(non_injected_job)

    # worker.perform_job(job, queue)
    worker.work(burst=True)

    assert job.return_value(refresh=True) is None
    cast(Mock, app_provider.app_mock).assert_not_called()


def test_task_without_injection(
    worker: Worker, queue: Queue, app_provider: AppProvider
):
    """Should run task without dependencies and without decorator."""
    worker.disable_default_exception_handler = True
    job = queue.enqueue(just_a_task)

    worker.work(burst=True)

    assert job.return_value(refresh=True) == "Just a task done"


def test_worker_missing_container(queue: Queue):
    """Should throw error if no container attached to worker."""
    exc_data = {}

    def exc_handler(job: Job, exc_type: type, exc_value: tuple, traceback: dict):
        exc_data["exc_type"] = exc_type
        exc_data["exc_value"] = exc_value

    worker = SimpleWorker(
        [queue], connection=queue.connection, exception_handlers=[exc_handler]
    )

    queue.enqueue(app_job)
    worker.work(burst=True)

    assert exc_data["exc_type"] is DishkaError
    assert exc_data["exc_value"].args[0] == "No container attached to Job."
