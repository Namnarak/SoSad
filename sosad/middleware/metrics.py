"""Metrics middleware — request timing and counters.

Usage::

    bot.use(sosad.middleware.metrics.request_metrics)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sosad.context.context import InteractionContext
from sosad.di.scopes import ScopeManager
from sosad.middleware.types import HandlerFunc

logger = logging.getLogger("sosad.metrics")


_metrics: dict[str, Any] = {
    "total_requests": 0,
    "total_errors": 0,
    "command_timings": {},
}


async def request_metrics(
    ctx: InteractionContext,
    next_fn: HandlerFunc,
    scope: ScopeManager,
) -> None:
    """Middleware that records request timing and counters.

    Adds timing data to the scope, accessible via DI.
    """
    _metrics["total_requests"] += 1
    start = time.monotonic()

    try:
        await next_fn(ctx, scope)
    except Exception:
        _metrics["total_errors"] += 1
        raise
    finally:
        elapsed = time.monotonic() - start
        cmd_name = getattr(ctx.interaction, "command_name", None) or "unknown"
        if cmd_name not in _metrics["command_timings"]:
            _metrics["command_timings"][cmd_name] = []
        timings = _metrics["command_timings"][cmd_name]
        timings.append(elapsed)
        # Keep only last 100 timings per command
        if len(timings) > 100:
            timings.pop(0)

        logger.debug(
            "Request: %s took %.2fms",
            cmd_name,
            elapsed * 1000,
        )


def get_metrics() -> dict[str, Any]:
    return _metrics


def reset_metrics() -> None:
    _metrics.clear()
    _metrics["total_requests"] = 0
    _metrics["total_errors"] = 0
    _metrics["command_timings"] = {}


__all__ = ["get_metrics", "request_metrics", "reset_metrics"]
