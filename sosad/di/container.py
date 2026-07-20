"""DI container with auto-resolution like FastAPI."""

from __future__ import annotations

import inspect
import logging
from typing import Any, TypeVar

from sosad.di.scopes import ScopeManager

logger = logging.getLogger("sosad.di")
T = TypeVar("T")


class Container:
    """DI container with auto-resolution from type annotations.

    Usage::

        container = Container()

        @container.singleton
        class Database:
            ...

        # In command handler — auto-resolved from annotation:
        async def ban(ctx, user, db: Database):
            await db.query(...)
    """

    def __init__(self) -> None:
        self._singletons: dict[type, type] = {}
        self._singleton_instances: dict[type, Any] = {}
        self._factories: dict[type, type] = {}
        self._values: dict[type, Any] = {}
        self._registry: dict[type, Any] = {}

    def singleton(self, cls: type[T]) -> type[T]:
        self._singletons[cls] = cls
        return cls

    def factory(self, cls: type[T]) -> type[T]:
        self._factories[cls] = cls
        return cls

    def value(self, cls: type[T], instance: T) -> None:
        self._values[cls] = instance

    def register(self, cls: type[T], instance: T) -> None:
        """Register an instance for a type (alias for value)."""
        self._values[cls] = instance

    def has(self, cls: type) -> bool:
        return cls in self._singletons or cls in self._factories or cls in self._values

    async def resolve(self, annotation: type[T], scope: ScopeManager) -> T:
        """Resolve a dependency by type annotation.

        Resolution order:
        1. Scoped values
        2. Pre-built values
        3. Singletons (created once)
        4. Factories (created per-request)
        5. Direct instantiation via __init__ introspection
        """
        scoped = scope.resolve(annotation)
        if scoped is not None:
            return scoped

        if annotation in self._values:
            return self._values[annotation]

        if annotation in self._singletons:
            if annotation not in self._singleton_instances:
                self._singleton_instances[annotation] = await self._create(
                    self._singletons[annotation], scope
                )
            return self._singleton_instances[annotation]

        if annotation in self._factories:
            return await self._create(self._factories[annotation], scope)

        try:
            return await self._create(annotation, scope)
        except (TypeError, ImportError) as exc:
            raise ValueError(
                f"Cannot resolve type {annotation.__name__}. "
                "Register it with @container.singleton, @container.factory, "
                "or container.value()."
            ) from exc

    async def _create(self, cls: type, scope: ScopeManager) -> Any:
        sig = inspect.signature(cls.__init__)  # type: ignore[misc]
        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.annotation is inspect.Parameter.empty:
                continue
            kwargs[name] = await self.resolve(param.annotation, scope)
        if inspect.iscoroutinefunction(cls.__init__):  # type: ignore[arg-type]
            return await cls(**kwargs)  # type: ignore[misc]
        return cls(**kwargs)


__all__ = ["Container"]
