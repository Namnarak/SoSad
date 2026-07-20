"""DI container with singleton, factory, and value registrations."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from sosad.di.scopes import ScopeManager

T = TypeVar("T")


class Container:
    """Global DI container. Holds singleton and factory registrations.

    Usage::

        container = Container()

        @container.singleton
        class Database:
            ...

        @container.factory
        class HttpClient:
            ...
    """

    def __init__(self) -> None:
        self._singletons: dict[type, Callable[..., Any]] = {}
        self._singleton_instances: dict[type, Any] = {}
        self._factories: dict[type, Callable[..., Any]] = {}
        self._values: dict[type, Any] = {}

    def singleton(self, cls: type[T]) -> type[T]:
        """Decorator: register a class as a singleton (created once)."""
        self._singletons[cls] = cls
        return cls

    def factory(self, cls: type[T]) -> type[T]:
        """Decorator: register a class as a factory (created per-request)."""
        self._factories[cls] = cls
        return cls

    def value(self, cls: type[T], instance: T) -> None:
        """Register a pre-built instance."""
        self._values[cls] = instance

    def has(self, cls: type) -> bool:
        """Check if a type is registered."""
        return cls in self._singletons or cls in self._factories or cls in self._values

    async def resolve(self, annotation: type[T], scope: ScopeManager) -> T:
        """Resolve a dependency by type annotation.

        Resolution order:
        1. Scoped values (from ScopeManager)
        2. Pre-built values
        3. Singletons (created once, cached)
        4. Factories (created per-request)
        5. Recursive __init__ introspection
        """
        # 1. Check scope
        scoped = scope.resolve(annotation)
        if scoped is not None:
            return scoped

        # 2. Check values
        if annotation in self._values:
            return self._values[annotation]

        # 3. Check singletons
        if annotation in self._singletons:
            if annotation not in self._singleton_instances:
                self._singleton_instances[annotation] = await self._create(
                    self._singletons[annotation], scope
                )
            return self._singleton_instances[annotation]

        # 4. Check factories
        if annotation in self._factories:
            return await self._create(self._factories[annotation], scope)

        # 5. Try to instantiate directly
        try:
            return await self._create(annotation, scope)  # type: ignore[return-value]
        except (TypeError, ImportError) as exc:
            raise ValueError(
                f"Cannot resolve type {annotation.__name__}. "
                "Register it with @container.singleton, @container.factory, or container.value()."
            ) from exc

    async def _create(self, cls: type, scope: ScopeManager) -> Any:
        """Create an instance by introspecting __init__ annotations."""
        sig = inspect.signature(cls.__init__)  # type: ignore[misc]
        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.annotation is inspect.Parameter.empty:
                continue
            kwargs[name] = await self.resolve(param.annotation, scope)
        if asyncio_iscoroutinefunction(cls.__init__):  # type: ignore[arg-type]
            return await cls(**kwargs)  # type: ignore[misc]
        return cls(**kwargs)


def asyncio_iscoroutinefunction(func: Any) -> bool:
    """Check if a function is a coroutine function."""
    return inspect.iscoroutinefunction(func)


__all__ = ["Container"]
