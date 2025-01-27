from collections.abc import Iterable
from typing import NewType, cast
from unittest.mock import Mock

from dishka import Provider, Scope, provide

AppDep = NewType("AppDep", str)
APP_DEP_VALUE = "APP"

RequestDep = NewType("RequestDep", str)
REQUEST_DEP_VALUE = "REQUEST"

AppMock = NewType("AppMock", Mock)


class AppProvider(Provider):
    def __init__(self):
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.websocket_released = Mock()
        self.mock = Mock()
        self.app_mock = AppMock(Mock())

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield cast(AppDep, APP_DEP_VALUE)
        self.app_released()

    @provide(scope=Scope.REQUEST)
    def request(self) -> Iterable[RequestDep]:
        yield cast(RequestDep, REQUEST_DEP_VALUE)
        self.request_released()

    @provide(scope=Scope.REQUEST)
    def mock(self) -> Mock:
        return cast(Mock, self.mock)

    @provide(scope=Scope.APP)
    def app_mock(self) -> AppMock:
        return cast(AppMock, self.app_mock)
