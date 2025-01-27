from dishka import Container, Provider, Scope, make_container, provide
from redis import Redis

from dishka_rq import DishkaWorker


class StrProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def hello(self) -> str:
        return "Hello"


def setup_worker(container: Container) -> DishkaWorker:
    queues = ["default"]
    conn = Redis()
    worker = DishkaWorker(container=container, queues=queues, connection=conn)
    return worker


def setup_container() -> Container:
    provider = StrProvider()
    container = make_container(provider)
    return container


if __name__ == "__main__":
    container = setup_container()
    worker = setup_worker(container)

    worker.work(with_scheduler=True)
