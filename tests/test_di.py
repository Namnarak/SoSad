"""Tests for the DI container."""

import pytest

from sosad.di.container import Container
from sosad.di.markers import inject
from sosad.di.scopes import ScopeManager


class FakeService:
    def __init__(self) -> None:
        self.value = 42


class DependentService:
    def __init__(self, dep: FakeService) -> None:
        self.dep = dep


def test_container_has():
    container = Container()
    container.value(FakeService, FakeService())
    assert container.has(FakeService)
    assert not container.has(str)


@pytest.mark.asyncio
async def test_container_resolve_value():
    container = Container()
    svc = FakeService()
    container.value(FakeService, svc)
    scope = ScopeManager()
    result = await container.resolve(FakeService, scope)
    assert result is svc
    assert result.value == 42


@pytest.mark.asyncio
async def test_container_resolve_singleton():
    container = Container()

    @container.singleton
    class MySingleton:
        pass

    scope = ScopeManager()
    a = await container.resolve(MySingleton, scope)
    b = await container.resolve(MySingleton, scope)
    assert a is b


@pytest.mark.asyncio
async def test_container_resolve_factory():
    container = Container()

    @container.factory
    class MyFactory:
        pass

    scope = ScopeManager()
    a = await container.resolve(MyFactory, scope)
    b = await container.resolve(MyFactory, scope)
    assert a is not b


def test_scope_set_and_resolve():
    scope = ScopeManager()
    svc = FakeService()
    scope.set(FakeService, svc)
    assert scope.resolve(FakeService) is svc
    assert scope.has(FakeService)
    assert scope.resolve(str) is None


def test_scope_cleanup():
    scope = ScopeManager()
    scope.set(FakeService, FakeService())
    assert scope.has(FakeService)
    scope.cleanup()
    assert not scope.has(FakeService)


def test_inject_marker():
    marker = inject()
    assert repr(marker) == "<inject>"
    assert marker is inject()
