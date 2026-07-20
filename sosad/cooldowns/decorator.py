"""Decorator for applying cooldowns to commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sosad.commands.models import SlashCommandMeta
from sosad.cooldowns.buckets import BucketScope, CooldownConfig


def cooldown(
    rate: int,
    period: float,
    bucket: BucketScope = BucketScope.USER,
    *,
    retry_after_message: str | None = None,
) -> Callable[[Any], Any]:
    """Decorator: apply cooldown to a command.

    Usage::

        @sosad.slash_command("work", "Earn coins")
        @sosad.cooldown(1, 60, bucket=BucketScope.USER)
        async def work(ctx: InteractionContext) -> None:
            ...
    """

    def decorator(func: Any) -> Any:
        _config = CooldownConfig(
            rate=rate,
            period=period,
            bucket=bucket,
            retry_after_message=retry_after_message,
        )
        if isinstance(func, SlashCommandMeta):
            return SlashCommandMeta(
                name=func.name,
                description=func.description,
                handler=func.handler,
                options=func.options,
                scopes=func.scopes,
                default_member_permissions=func.default_member_permissions,
                is_dm_only=func.is_dm_only,
                nsfw=func.nsfw,
            )
        return func

    return decorator


__all__ = ["cooldown"]
