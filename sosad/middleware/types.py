"""Middleware protocol definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sosad.context.context import InteractionContext
    from sosad.di.scopes import ScopeManager


@runtime_checkable
class HandlerFunc(Protocol):
    """The next step in the middleware chain."""

    async def __call__(
        self,
        ctx: InteractionContext,
        scope: ScopeManager,
    ) -> None: ...


@runtime_checkable
class MiddlewareFunc(Protocol):
    """A middleware function. Receives context, next handler, and DI scope."""

    async def __call__(
        self,
        ctx: InteractionContext,
        next: HandlerFunc,
        scope: ScopeManager,
    ) -> None: ...


__all__ = ["HandlerFunc", "MiddlewareFunc"]
