"""SoSad exception hierarchy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sosad.context.context import InteractionContext


class SoSadError(Exception):
    """Base exception for all SoSad errors."""


class CommandError(SoSadError):
    """Error during command execution."""

    def __init__(self, message: str, *, ctx: InteractionContext | None = None) -> None:
        super().__init__(message)
        self.ctx = ctx


class CheckFailed(CommandError):
    """A pre-condition check failed."""


class RateLimited(CommandError):
    """Cooldown exceeded."""

    def __init__(
        self,
        message: str | None = None,
        *,
        retry_after: float = 0.0,
        ctx: InteractionContext | None = None,
    ) -> None:
        super().__init__(message or f"Rate limited. Try again in {retry_after:.1f}s", ctx=ctx)
        self.retry_after = retry_after


class CommandNotFound(SoSadError):
    """No handler found for the interaction."""


class SyncError(SoSadError):
    """Error during command sync."""


__all__ = [
    "CheckFailed",
    "CommandError",
    "CommandNotFound",
    "RateLimited",
    "SoSadError",
    "SyncError",
]
