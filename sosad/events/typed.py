"""Generic decorator for typed event listening."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import hikari

from sosad.events.models import EventListenerMeta
from sosad.events.registration import register_listener

E = TypeVar("E", bound=hikari.Event)


def listen[E: hikari.Event](
    event_type: type[E],
) -> Callable[[Callable[..., Any]], EventListenerMeta]:
    """Decorator for typed event listening.

    Usage::

        @sosad.listen(hikari.GuildMessageCreateEvent)
        async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
            print(event.message.content)
    """

    def decorator(func: Callable[..., Any]) -> EventListenerMeta:
        meta = EventListenerMeta(
            event_type=event_type,
            handler=func,
            name=func.__name__,
        )
        register_listener(meta)
        return meta

    return decorator


__all__ = ["listen"]
