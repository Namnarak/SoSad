"""Per-request scoped dependency storage."""

from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")


class ScopeManager:
    """Per-request scoped dependency storage.

    Created for each interaction request. Holds request-scoped values
    that are cleaned up after the request completes.
    """

    def __init__(self) -> None:
        self._scoped: dict[type, Any] = {}

    def set(self, cls: type[T], instance: T) -> None:
        """Set a scoped value (e.g., InteractionContext)."""
        self._scoped[cls] = instance

    def resolve(self, annotation: type[T]) -> T | None:
        """Check if a scoped value exists for this type."""
        return self._scoped.get(annotation)  # type: ignore[return-value]

    def has(self, annotation: type) -> bool:
        """Check if a scoped value exists."""
        return annotation in self._scoped

    def cleanup(self) -> None:
        """Release all scoped resources."""
        self._scoped.clear()


__all__ = ["ScopeManager"]
