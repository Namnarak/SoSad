"""Registration helpers for the DI container."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sosad.di.container import Container


def singleton(container: Container) -> Any:
    """Register a class as a singleton."""
    return container.singleton


def factory(container: Container) -> Any:
    """Register a class as a factory."""
    return container.factory


def value(container: Container, cls: type, instance: Any) -> None:
    """Register a pre-built instance."""
    container.value(cls, instance)


__all__ = ["factory", "singleton", "value"]
