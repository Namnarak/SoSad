"""discord.py-compatible utility functions."""

from __future__ import annotations

import datetime as _dt
import re as _re
from collections.abc import Callable, Iterable
from typing import Any


def get[T](iterable: Iterable[T], **attrs: Any) -> T | None:
    """Find the first element in iterable matching all keyword attributes.

    Usage::

        user = discord.utils.get(members, id=12345)
        channel = discord.utils.get(channels, name="general")
    """
    for item in iterable:
        if all(getattr(item, k, _MISSING) == v for k, v in attrs.items()):
            return item
    return None


def find[T](predicate: Callable[[T], bool], iterable: Iterable[T]) -> T | None:
    """Find the first element where predicate returns True."""
    for item in iterable:
        if predicate(item):
            return item
    return None


_MISSING = object()


def _escape(text: str, *, markdown: bool = False, mentions: bool = False) -> str:
    if markdown:
        text = _re.sub(r"([*_`~|>#\\])", r"\\\1", text)
    if mentions:
        text = _re.sub(r"@(everyone|here|&?\d+)", "@\u200b\\1", text)
    return text


def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    return _escape(text, markdown=True)


def escape_mentions(text: str) -> str:
    """Escape @everyone, @here, and role/user mentions."""
    return _escape(text, mentions=True)


def escape_markdown_and_mentions(text: str) -> str:
    """Escape both markdown and mentions."""
    return _escape(text, markdown=True, mentions=True)


def utcnow() -> _dt.datetime:
    """Return the current UTC datetime."""
    return _dt.datetime.now(_dt.UTC)


def format_dt(dt: _dt.datetime, style: str = "f") -> str:
    """Format a datetime as a Discord timestamp."""
    ts = int(dt.timestamp())
    return f"<t:{ts}:{style}>"


def snowflake_time(id: int) -> _dt.datetime:
    """Get the datetime from a Discord snowflake."""
    return _dt.datetime.fromtimestamp(
        ((id >> 22) + 1420070400000) / 1000,
        tz=_dt.UTC,
    )


__all__ = [
    "get",
    "find",
    "escape_markdown",
    "escape_mentions",
    "escape_markdown_and_mentions",
    "utcnow",
    "format_dt",
    "snowflake_time",
]
