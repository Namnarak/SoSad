"""Routes InteractionCreateEvent to the correct handler through middleware."""

from __future__ import annotations

import inspect
import logging
from typing import Any

import hikari

from sosad.context.context import InteractionContext
from sosad.di.markers import _InjectMarker
from sosad.di.scopes import ScopeManager

if __name__ != "__main__":
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from sosad.commands.registry import CommandRegistry
        from sosad.core.client import Client
        from sosad.middleware.types import HandlerFunc

logger = logging.getLogger("sosad.router")


def _extract_option_values(
    interaction: hikari.CommandInteraction,
    handler: Any,
) -> dict[str, Any]:
    """Extract option values from an interaction, matching them to handler parameters."""
    options_list = interaction.options or []
    option_map: dict[str, Any] = {}
    resolved = interaction.resolved

    for opt in options_list:
        if opt.type in (
            hikari.OptionType.SUB_COMMAND,
            hikari.OptionType.SUB_COMMAND_GROUP,
        ):
            if opt.options:
                for sub_opt in opt.options:
                    option_map[sub_opt.name] = _resolve_value(sub_opt, resolved)
            continue
        option_map[opt.name] = _resolve_value(opt, resolved)

    return option_map


def _resolve_value(
    option: hikari.CommandInteractionOption,
    resolved: hikari.ResolvedOptionData | None,
) -> Any:
    """Resolve a single option value, handling types that need resolved data."""
    value = option.value

    if resolved is None:
        return value

    if (
        option.type in (hikari.OptionType.USER, hikari.OptionType.MENTIONABLE)
        and isinstance(value, hikari.Snowflake)
    ):
        member = resolved.members.get(value)
        if member is not None:
            return member
        user = resolved.users.get(value)
        if user is not None:
            return user

    if (
        option.type == hikari.OptionType.CHANNEL
        and isinstance(value, hikari.Snowflake)
    ):
        channel = resolved.channels.get(value)
        if channel is not None:
            return channel

    if (
        option.type == hikari.OptionType.ROLE
        and isinstance(value, hikari.Snowflake)
    ):
        role = resolved.roles.get(value)
        if role is not None:
            return role

    return value


def build_handler_args(
    ctx: InteractionContext,
    interaction: hikari.CommandInteraction,
    handler: Any,
    scope: ScopeManager,
) -> dict[str, Any]:
    """Build the argument dict for calling a command handler."""
    option_values = _extract_option_values(interaction, handler)
    kwargs: dict[str, Any] = {}

    sig = inspect.signature(handler)
    for name, param in sig.parameters.items():
        if name == "ctx":
            kwargs["ctx"] = ctx
            continue

        if isinstance(param.default, _InjectMarker):
            continue

        if name in option_values:
            kwargs[name] = option_values[name]

    return kwargs


class CommandRouter:
    """Routes InteractionCreateEvent to the correct handler through middleware.

    Usage::

        router = CommandRouter(registry, client, pipeline)
        await router.handle_interaction(event)
    """

    def __init__(
        self,
        registry: CommandRegistry,
        client: Client,
        pipeline: HandlerFunc,
    ) -> None:
        self._registry = registry
        self._client = client
        self._pipeline = pipeline

    async def handle_interaction(
        self, event: hikari.InteractionCreateEvent
    ) -> None:
        """Entry point for all interaction events."""
        interaction = event.interaction
        if not isinstance(interaction, hikari.CommandInteraction):
            return

        meta = self._registry.resolve(interaction)
        if meta is None:
            logger.warning("Unknown command: %s", interaction.command_name)
            return

        ctx = InteractionContext(
            interaction=interaction,
            client=self._client,
            app=self._client.app,
        )

        scope = ScopeManager()

        try:
            await self._pipeline(ctx, scope)
        except Exception:
            logger.exception(
                "Error handling command %s", interaction.command_name
            )
        finally:
            scope.cleanup()


__all__ = ["CommandRouter", "build_handler_args"]
