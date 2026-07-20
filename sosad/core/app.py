"""Application state container."""

from __future__ import annotations

from typing import Any


class App:
    """Shared application state. Holds objects available to all components."""

    def __init__(self) -> None:
        self._state: dict[type, Any] = {}

    def set(self, key: type, value: Any) -> None:
        """Store a value by type key."""
        self._state[key] = value

    def get(self, key: type, default: Any = None) -> Any:
        """Retrieve a value by type key."""
        return self._state.get(key, default)

    def has(self, key: type) -> bool:
        """Check if a key exists."""
        return key in self._state

    def remove(self, key: type) -> None:
        """Remove a key."""
        self._state.pop(key, None)

    def clear(self) -> None:
        """Clear all state."""
        self._state.clear()


__all__ = ["App"]
