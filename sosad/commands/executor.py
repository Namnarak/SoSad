"""Command executor — invokes handlers with resolved arguments."""

from __future__ import annotations

import logging
from typing import Any

from sosad.commands.models import SlashCommandMeta, SubCommandMeta
from sosad.commands.router import build_handler_args, get_di_params
from sosad.context.context import InteractionContext
from sosad.di.scopes import ScopeManager

logger = logging.getLogger("sosad.executor")


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
