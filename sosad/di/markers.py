"""DI markers and sentinel values."""

from __future__ import annotations

from typing import Any


class _InjectMarker:
    """Sentinel for DI resolution in function parameters.

    Usage::

        async def ban(
            ctx: InteractionContext,
            user: hikari.User,
            db: Database = inject(),
        ) -> None:
            ...
    """

    _instance: _InjectMarker | None = None

    def __new__(cls) -> _InjectMarker:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<inject>"

    def __class_getitem__(cls, item: Any) -> Any:
        return item


def inject() -> Any:
    """Marker for DI resolution in function parameters."""
    return _InjectMarker()


__all__ = ["inject"]
