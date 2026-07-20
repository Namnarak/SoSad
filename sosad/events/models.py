"""Event metadata."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EventListenerMeta:
    """Metadata for an event listener."""

    event_type: type
    handler: Callable[..., Any]
    name: str | None = None


__all__ = ["EventListenerMeta"]
