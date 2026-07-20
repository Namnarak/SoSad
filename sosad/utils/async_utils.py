"""Async utility helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


async def maybe_await(func: Callable[..., Any], *args: Any) -> Any:
    """Call a function and await the result if it's a coroutine."""
    result = func(*args)
    if asyncio.iscoroutine(result):
        return await result
    return result


__all__ = ["maybe_await"]
