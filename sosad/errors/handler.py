"""Error pipeline — catch, transform, and respond."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sosad.errors.builtin import default_error_handler

logger = logging.getLogger("sosad.errors")

ErrorHandler = Callable[[Exception, Any], Awaitable[None]]


class ErrorPipeline:
    """Collects error handlers and runs them in order.

    Usage::

        pipeline = ErrorPipeline()
        pipeline.on(CheckFailed, my_check_handler)
        await pipeline.handle(error, ctx)
    """

    def __init__(self) -> None:
        self._handlers: list[tuple[type[Exception], ErrorHandler]] = []
        self._default = default_error_handler

    def on(self, error_type: type[Exception], handler: ErrorHandler) -> None:
        """Register a handler for a specific exception type."""
        self._handlers.append((error_type, handler))

    def set_default(self, handler: ErrorHandler) -> None:
        """Set the default error handler."""
        self._default = handler

    async def handle(self, error: Exception, ctx: Any = None) -> None:
        """Run the error through the handler chain."""
        for error_type, handler in self._handlers:
            if isinstance(error, error_type):
                try:
                    await handler(error, ctx)
                except Exception:
                    logger.exception("Error in error handler")
                return

        # Default handler
        try:
            await self._default(error, ctx)
        except Exception:
            logger.exception("Error in default error handler")


__all__ = ["ErrorPipeline"]
