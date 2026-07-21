"""Routes interactions to the correct handler through middleware."""

from __future__ import annotations

import inspect
import logging
from typing import Any

import hikari

from sosad.context.context import InteractionContext
from sosad.di.scopes import ScopeManager

if __name__ != "__main__":
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from sosad.commands.registry import CommandRegistry
        from sosad.core.base_client import BaseClient
        from sosad.middleware.types import HandlerFunc

logger = logging.getLogger("sosad.router")

_PRIMITIVE_TYPES = frozenset({
    str, int, float, bool,
    hikari.User, hikari.Member,
    hikari.GuildChannel, hikari.Role, hikari.Attachment,
})

_FRAMEWORK_TYPES = frozenset({InteractionContext})


def _extract_option_values(
    interaction: hikari.CommandInteraction,
    handler: Any,
) -> dict[str, Any]:
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


def _resolve_annotations(
    handler: Any,
) -> dict[str, type]:
    import typing
    try:
        return typing.get_type_hints(handler)
    except Exception:
        return {}


def build_handler_args(
    ctx: InteractionContext,
    interaction: hikari.CommandInteraction,
    handler: Any,
    scope: ScopeManager,
) -> dict[str, Any]:
    option_values = _extract_option_values(interaction, handler)
    kwargs: dict[str, Any] = {}
    hints = _resolve_annotations(handler)

    sig = inspect.signature(handler)
    for name, param in sig.parameters.items():
        if name == "ctx":
            kwargs["ctx"] = ctx
            continue
        ann = hints.get(name, param.annotation)
        if ann in _FRAMEWORK_TYPES:
            kwargs["ctx"] = ctx
            continue

    for name in option_values:
        if name not in kwargs:
            kwargs[name] = option_values[name]

    return kwargs


def get_di_params(handler: Any) -> dict[str, inspect.Parameter]:
    hints = _resolve_annotations(handler)
    sig = inspect.signature(handler)
    di_params: dict[str, inspect.Parameter] = {}
    for name, param in sig.parameters.items():
        if name in ("ctx", "self", "cls"):
            continue
        if param.annotation is inspect.Parameter.empty:
            continue
        ann = hints.get(name, param.annotation)
        if ann in _FRAMEWORK_TYPES:
            continue
        if ann in _PRIMITIVE_TYPES:
            continue
        di_params[name] = param
    return di_params


class CommandRouter:
    """Routes interactions to the correct handler through middleware.

    Supports both Gateway (via events) and REST (via direct interaction objects).
    """

    def __init__(
        self,
        registry: CommandRegistry,
        client: BaseClient,
        pipeline: HandlerFunc,
    ) -> None:
        self._registry = registry
        self._client = client
        self._pipeline = pipeline

    async def handle_interaction(
        self, event: hikari.InteractionCreateEvent
    ) -> None:
        """Handle an interaction from Gateway (via InteractionCreateEvent)."""
        interaction = event.interaction
        await self._handle_raw_interaction(interaction)

    async def handle_interaction_event(
        self,
        interaction: hikari.CommandInteraction,
    ) -> None:
        """Handle a direct interaction (from REST or other sources)."""
        await self._handle_raw_interaction(interaction)

    async def handle_component_interaction(
        self,
        interaction: hikari.ComponentInteraction,
    ) -> None:
        """Handle a component interaction (button/select) from REST."""
        await self._route_component(interaction)

    async def handle_modal_interaction(
        self,
        interaction: hikari.ModalInteraction,
    ) -> None:
        """Handle a modal interaction from REST."""
        await self._route_modal(interaction)

    async def handle_autocomplete_interaction(
        self,
        interaction: hikari.AutocompleteInteraction,
    ) -> None:
        """Handle an autocomplete interaction from REST."""
        await self._route_autocomplete(interaction)

    async def _handle_raw_interaction(
        self,
        interaction: hikari.CommandInteraction,
    ) -> None:
        """Core interaction handler — shared by Gateway and REST."""
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

    async def _route_component(
        self,
        interaction: hikari.ComponentInteraction,
    ) -> None:
        """Route a component interaction to its registered handler."""
        from sosad.components.registry import ComponentRegistry

        registry = ComponentRegistry.get_instance()
        handler = registry.get_handler(interaction.custom_id)

        if handler is None:
            logger.warning("No handler for component: %s", interaction.custom_id)
            return

        ctx = InteractionContext(
            interaction=interaction,
            client=self._client,
            app=self._client.app,
        )

        scope = ScopeManager()

        try:
            await handler(ctx, scope)
        except Exception:
            logger.exception("Error handling component %s", interaction.custom_id)
        finally:
            scope.cleanup()

    async def _route_modal(
        self,
        interaction: hikari.ModalInteraction,
    ) -> None:
        """Route a modal interaction to its registered handler."""
        from sosad.components.registry import ComponentRegistry

        registry = ComponentRegistry.get_instance()
        handler = registry.get_modal_handler(interaction.custom_id)

        if handler is None:
            logger.warning("No handler for modal: %s", interaction.custom_id)
            return

        ctx = InteractionContext(
            interaction=interaction,
            client=self._client,
            app=self._client.app,
        )

        scope = ScopeManager()

        try:
            await handler(ctx, scope)
        except Exception:
            logger.exception("Error handling modal %s", interaction.custom_id)
        finally:
            scope.cleanup()

    async def _route_autocomplete(
        self,
        interaction: hikari.AutocompleteInteraction,
    ) -> None:
        """Route an autocomplete interaction."""
        logger.warning("Autocomplete not yet implemented for: %s", interaction.command_name)
        await interaction.create_response([])


__all__ = [
    "CommandRouter",
    "build_handler_args",
    "get_di_params",
]
