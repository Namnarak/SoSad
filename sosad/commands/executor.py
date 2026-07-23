"""Command executor — invokes handlers with resolved arguments."""

from __future__ import annotations

import logging
from typing import Any

from sosad.commands.models import SlashCommandMeta, SubCommandMeta
from sosad.commands.router import build_handler_args, get_di_params
from sosad.context.context import InteractionContext
from sosad.cooldowns.buckets import BucketScope
from sosad.cooldowns.storage import InMemoryCooldownStorage
from sosad.di.scopes import ScopeManager
from sosad.errors.base import CheckFailed, RateLimited

logger = logging.getLogger("sosad.executor")
_cooldowns = InMemoryCooldownStorage()


def _cooldown_key(meta: SlashCommandMeta | SubCommandMeta, ctx: InteractionContext) -> str:
    config = meta.cooldown
    assert config is not None
    if config.bucket is BucketScope.USER:
        subject = ctx.author.id
    elif config.bucket is BucketScope.GUILD:
        subject = ctx.guild_id or ctx.author.id
    elif config.bucket is BucketScope.CHANNEL:
        subject = ctx.channel_id
    elif config.bucket is BucketScope.MEMBER:
        subject = f"{ctx.guild_id or 'dm'}:{ctx.author.id}"
    else:
        subject = ctx.author.id
    return f"{meta.name}:{config.bucket.value}:{subject}"


async def execute_command(
    meta: SlashCommandMeta | SubCommandMeta,
    ctx: InteractionContext,
    scope: ScopeManager,
    container: Any = None,
) -> None:
    """Execute a command handler with proper argument resolution.

    Auto-resolution (FastAPI-style):
    - 'ctx' → from scope
    - Interaction options → from interaction
    - Complex types → from DI container automatically
    """
    handler = meta.handler

    for check in meta.checks:
        result = await check(ctx)
        if not result.passed:
            raise CheckFailed(result.reason or "A check failed.", ctx=ctx)

    if meta.cooldown is not None:
        result = await _cooldowns.acquire(_cooldown_key(meta, ctx), meta.cooldown)
        if not result.allowed:
            raise RateLimited(
                meta.cooldown.retry_after_message,
                retry_after=result.retry_after,
                ctx=ctx,
            )

    interaction = ctx.interaction
    kwargs = build_handler_args(ctx, interaction, handler, scope)

    # Auto-resolve DI parameters without inject() marker
    if container is not None:
        di_params = get_di_params(handler)
        for name, param in di_params.items():
            if name not in kwargs:
                try:
                    kwargs[name] = await container.resolve(param.annotation, scope)
                except (ValueError, TypeError):
                    logger.debug(
                        "Could not resolve DI parameter '%s' (type=%s)",
                        name,
                        getattr(param.annotation, "__name__", str(param.annotation)),
                    )

    await handler(**kwargs)


__all__ = ["execute_command"]
