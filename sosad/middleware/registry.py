"""Middleware stack builder — composes middleware into a single handler."""

from __future__ import annotations

from typing import Any

from sosad.middleware.types import HandlerFunc, MiddlewareFunc


class MiddlewareStack:
    """Builds and runs the middleware pipeline.

    Usage::

        stack = MiddlewareStack()
        stack.add(logging_middleware)
        stack.add(check_middleware)
        handler = stack.build()
        await handler(ctx, scope)
    """

    def __init__(self) -> None:
        self._middlewares: list[MiddlewareFunc] = []
        self._final_handler: HandlerFunc | None = None

    def add(self, middleware: MiddlewareFunc) -> None:
        """Add a middleware to the stack."""
        self._middlewares.append(middleware)

    def set_handler(self, handler: HandlerFunc) -> None:
        """Set the final handler at the end of the pipeline."""
        self._final_handler = handler

    def build(self) -> HandlerFunc:
        """Returns the composed handler. Last-added wraps first."""
        if self._final_handler is None:
            raise RuntimeError("No final handler set. Call set_handler() first.")

        handler: HandlerFunc = self._final_handler
        for mw in reversed(self._middlewares):
            handler = _wrap(mw, handler)
        return handler

    def clear(self) -> None:
        """Clear all middleware and the final handler."""
        self._middlewares.clear()
        self._final_handler = None


def _wrap(middleware: MiddlewareFunc, next_handler: HandlerFunc) -> HandlerFunc:
    """Wrap a middleware around the next handler."""

    async def wrapped(ctx: Any, scope: Any) -> None:
        await middleware(ctx, next_handler, scope)

    return wrapped


__all__ = ["MiddlewareStack"]
