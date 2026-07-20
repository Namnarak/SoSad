"""Command executor — invokes handlers with resolved arguments."""

from __future__ import annotations

import inspect
import logging
from typing import Any

import hikari

from sosad.commands.models import SlashCommandMeta, SubCommandMeta
from sosad.commands.router import build_handler_args
from sosad.context.context import InteractionContext
from sosad.di.markers import _InjectMarker
from sosad.di.scopes import ScopeManager

logger = logging.getLogger("sosad.executor")


def _get_subcommand_interaction(
    interaction: hikari.CommandInteraction,
) -> hikari.CommandInteractionOption | None:
    """Extract the subcommand option from a group interaction."""
    for opt in (interaction.options or ()):
        if opt.type == hikari.OptionType.SUB_COMMAND:
            return opt
    return None


async def execute_command(
    meta: SlashCommandMeta | SubCommandMeta,
    ctx: InteractionContext,
    scope: ScopeManager,
    container: Any = None,
) -> None:
    """Execute a command handler with proper argument resolution.

    1. Extract option values from the interaction
    2. Resolve DI dependencies from the container
    3. Call the handler
    """
    handler = meta.handler
    interaction = ctx.interaction

    kwargs = build_handler_args(ctx, interaction, handler, scope)

    # Resolve inject() parameters from DI container
    if container is not None:
        sig = inspect.signature(handler)
        for name, param in sig.parameters.items():
            if isinstance(param.default, _InjectMarker):
                try:
                    kwargs[name] = await container.resolve(param.annotation, scope)
                except (ValueError, TypeError):
                    logger.warning(
                        "Could not resolve DI parameter '%s' for command %s",
                        name,
                        getattr(meta, "name", "unknown"),
                    )

    await handler(**kwargs)


__all__ = ["execute_command"]
