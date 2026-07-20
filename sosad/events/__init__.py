"""Typed event system."""
from sosad.events.dispatcher import EventDispatcher
from sosad.events.typed import listen

__all__ = ["EventDispatcher", "listen"]
