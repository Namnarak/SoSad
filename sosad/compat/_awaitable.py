"""Small awaitable helpers used by the discord.py compatibility API."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Generator
from typing import Any


class DeferredAwaitable:
    """Create the underlying coroutine only when the value is awaited."""

    def __init__(self, factory: Callable[[], Awaitable[Any]]) -> None:
        self._factory = factory

    def __await__(self) -> Generator[Any, None, Any]:
        return self._factory().__await__()


class ImmediateAwaitable:
    """An awaitable for work that has already completed synchronously."""

    def __init__(self, value: Any = None) -> None:
        self._value = value

    def __await__(self) -> Generator[Any, None, Any]:
        async def done() -> Any:
            return self._value

        return done().__await__()


__all__ = ["DeferredAwaitable", "ImmediateAwaitable"]
