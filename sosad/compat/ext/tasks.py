"""discord.py-compatible background task loops."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from datetime import time as datetime_time
from typing import Any


class Loop:
    """Descriptor implementing the commonly used ``@tasks.loop`` API."""

    def __init__(
        self,
        callback: Callable[..., Any],
        *,
        seconds: float = 0.0,
        count: int | None = None,
        time: datetime_time | None = None,
    ) -> None:
        self.callback = callback
        self.seconds = seconds
        self.count = count
        self.time = time
        self.before_loop_callback: Callable[..., Any] | None = None
        self.after_loop_callback: Callable[..., Any] | None = None
        self.error_callback: Callable[..., Any] | None = None
        self._task: asyncio.Task[Any] | None = None

    def __get__(self, instance: Any, owner: type | None = None) -> Loop | BoundLoop:
        if instance is None:
            return self
        return BoundLoop(self, instance)

    def before_loop(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        self.before_loop_callback = callback
        return callback

    def after_loop(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        self.after_loop_callback = callback
        return callback

    def error(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        self.error_callback = callback
        return callback


class BoundLoop:
    def __init__(self, loop: Loop, instance: Any) -> None:
        self._loop = loop
        self._instance = instance

    @property
    def current_loop(self) -> int:
        return 0

    def start(self, *args: Any, **kwargs: Any) -> asyncio.Task[Any]:
        if self._loop._task is not None and not self._loop._task.done():
            return self._loop._task
        self._loop._task = asyncio.create_task(self._run(*args, **kwargs))
        return self._loop._task

    def cancel(self) -> None:
        if self._loop._task is not None:
            self._loop._task.cancel()

    def restart(self, *args: Any, **kwargs: Any) -> asyncio.Task[Any]:
        self.cancel()
        return self.start(*args, **kwargs)

    def is_running(self) -> bool:
        return self._loop._task is not None and not self._loop._task.done()

    def get_task(self) -> asyncio.Task[Any] | None:
        return self._loop._task

    async def _run(self, *args: Any, **kwargs: Any) -> None:
        callback = self._loop.callback.__get__(self._instance, type(self._instance))
        before = self._loop.before_loop_callback
        if before is not None:
            result = before(self._instance)
            if inspect.isawaitable(result):
                await result

        iteration = 0
        try:
            while self._loop.count is None or iteration < self._loop.count:
                try:
                    result = callback(*args, **kwargs)
                    if inspect.isawaitable(result):
                        await result
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    if self._loop.error_callback is not None:
                        result = self._loop.error_callback(self._instance, exc)
                        if inspect.isawaitable(result):
                            await result
                    else:
                        raise
                iteration += 1
                if self._loop.count is not None and iteration >= self._loop.count:
                    break
                await asyncio.sleep(self._loop.seconds)
        finally:
            after = self._loop.after_loop_callback
            if after is not None:
                result = after(self._instance)
                if inspect.isawaitable(result):
                    await result


def loop(
    *,
    seconds: float = 0.0,
    minutes: float = 0.0,
    hours: float = 0.0,
    time: datetime_time | None = None,
    count: int | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Loop]:
    del kwargs
    interval = seconds + (minutes * 60.0) + (hours * 3600.0)
    if interval <= 0 and time is None:
        interval = 1.0

    def decorator(callback: Callable[..., Any]) -> Loop:
        return Loop(callback, seconds=interval, count=count, time=time)

    return decorator


__all__ = ["BoundLoop", "Loop", "loop"]
