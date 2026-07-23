"""Decorator for applying cooldowns to commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from sosad.commands.models import SlashCommandMeta, SubCommandMeta
from sosad.commands.registration import register_command
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
        config = CooldownConfig(
            rate=rate,
            period=period,
            bucket=bucket,
            retry_after_message=retry_after_message,
        )
        if isinstance(func, (SlashCommandMeta, SubCommandMeta)):
            meta = replace(func, cooldown=config)
            register_command(meta)
            return meta
        func.__sosad_cooldown__ = config
        return func

    return decorator


__all__ = ["cooldown"]
