"""Global event listener registry."""

from __future__ import annotations

from sosad.events.models import EventListenerMeta

_listeners: list[EventListenerMeta] = []


def register_listener(meta: EventListenerMeta) -> None:
    """Add a listener to the global registry."""
    _listeners.append(meta)


def get_listeners() -> list[EventListenerMeta]:
    """Get all registered listeners."""
    return list(_listeners)


__all__ = ["get_listeners", "register_listener"]
