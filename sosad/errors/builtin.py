"""Built-in error responses."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sosad.context.context import InteractionContext


async def default_error_handler(error: Exception, ctx: InteractionContext) -> None:
    """Default error handler — sends an ephemeral error message."""
    from sosad.errors.base import CheckFailed, RateLimited

    if isinstance(error, CheckFailed):
        message = str(error) or "A check failed."
    elif isinstance(error, RateLimited):
        message = str(error) or "You're using this command too fast."
    else:
        message = "An unexpected error occurred."

    with contextlib.suppress(Exception):
        await ctx.respond().content(message).ephemeral().send()


__all__ = ["default_error_handler"]
