"""Decorator-based task registration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sosad.tasks.base import TaskMeta


def task(
    interval: float,
    *,
    delay: float = 0.0,
    once: bool = False,
    autostart: bool = True,
    name: str | None = None,
) -> Callable[[Any], TaskMeta]:
    """Decorator that registers a periodic background task.

    Usage::

        @sosad.task(interval=300)  # every 5 minutes
        async def cleanup():
            await db.cleanup_old_records()

        @sosad.task(interval=60, once=True, name="startup_check")
        async def startup():
            await check_api_health()
    """

    def decorator(func: Any) -> TaskMeta:
        meta = TaskMeta(
            name=name or func.__name__,
            handler=func,
            interval=interval,
            delay=delay,
            once=once,
            autostart=autostart,
        )
        return meta

    return decorator


def loop(
    interval: float,
    *,
    delay: float = 0.0,
    name: str | None = None,
) -> Callable[[Any], TaskMeta]:
    """Alias for @task (more explicit naming for recurring tasks)."""
    return task(interval, delay=delay, once=False, name=name)


__all__ = ["loop", "task"]
