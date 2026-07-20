"""Event dispatcher — hooks into hikari and routes to typed listeners."""

from __future__ import annotations

import logging
from typing import Any

import hikari

from sosad.events.models import EventListenerMeta
from sosad.events.registration import get_listeners

logger = logging.getLogger("sosad.events")


class EventDispatcher:
    """Wraps hikari's event dispatch with typed routing.

    Usage::

        dispatcher = EventDispatcher()
        dispatcher.attach(bot)
    """

    def __init__(self) -> None:
        self._listeners: dict[type[hikari.Event], list[EventListenerMeta]] = {}

    def load_from_registry(self) -> None:
        """Load all listeners from the global registry."""
        for meta in get_listeners():
            if meta.event_type not in self._listeners:
                self._listeners[meta.event_type] = []
            self._listeners[meta.event_type].append(meta)

    def attach(self, bot: hikari.GatewayBot) -> None:
        """Hook into hikari's event system and route to typed listeners."""
        self.load_from_registry()

        for event_type, listeners in self._listeners.items():
            for meta in listeners:
                bot.listen(event_type)(self._make_handler(meta.handler))
                logger.debug(
                    "Registered listener %s for %s",
                    meta.name or meta.handler.__name__,
                    event_type.__name__,
                )

    def _make_handler(self, handler: Any) -> Any:
        """Create a handler wrapper."""

        async def wrapped(event: hikari.Event) -> None:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Error in event listener %s",
                    handler.__name__,
                )

        return wrapped


__all__ = ["EventDispatcher"]
