from unittest.mock import Mock

from dishka import FromDishka

from dishka_rq import inject

from .common import AppDep, AppMock, RequestDep


@inject
def app_job(a: FromDishka[AppDep], app_mock: FromDishka[AppMock]) -> str:
    app_mock(a)
    return "App Job Done"


@inject
def request_job(
    a: FromDishka[AppDep],
    r: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> str:
    mock(r)
    return "Request Job Done"


def non_injected_job(a: FromDishka[AppDep], app_mock: FromDishka[AppMock]) -> str:
    app_mock(a)
    return "Non-injected job done"


def just_a_task() -> str:
    return "Just a task done"
