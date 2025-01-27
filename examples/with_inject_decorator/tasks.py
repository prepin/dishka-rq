from dishka import FromDishka

from dishka_rq import inject


@inject
def hello_world(hello: FromDishka[str]):
    return f"{hello} world!"
