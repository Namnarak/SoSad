"""Built-in middleware functions."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from sosad.middleware.types import HandlerFunc

if TYPE_CHECKING:
    from sosad.context.context import InteractionContext
    from sosad.di.scopes import ScopeManager

logger = logging.getLogger("sosad.middleware")


async def logging_middleware(
    ctx: InteractionContext,
    next: HandlerFunc,
    scope: ScopeManager,
) -> None:
    """Log command invocation with timing."""
    start = time.monotonic()
    command_name = ctx.interaction.command_name or "unknown"
    try:
        await next(ctx, scope)
    finally:
        elapsed = (time.monotonic() - start) * 1000
        logger.info("%s completed in %.2fms", command_name, elapsed)


__all__ = ["logging_middleware"]
