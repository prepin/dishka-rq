from dishka import Container, Provider, Scope, make_container, provide
from redis import Redis
from rq import Worker

from dishka_rq.rq_integration import setup_dishka


class StrProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def hello(self) -> str:
        return "Hello"


def setup_container() -> Container:
    provider = StrProvider()
    container = make_container(provider)
    return container


if __name__ == "__main__":
    worker = Worker(queues=["default"], connection=Redis())
    container = setup_container()
    setup_dishka(worker, container)

    worker.work(with_scheduler=True)
