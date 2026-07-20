"""Decorator-based command registration API."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from typing import Any

import hikari

from sosad.commands.models import (
    CommandGroupMeta,
    OptionDescriptor,
    SlashCommandMeta,
    SubCommandMeta,
)
from sosad.commands.registration import register_command

# Maps Python types → Hikari option types
_TYPE_MAP: dict[type, hikari.OptionType] = {
    str: hikari.OptionType.STRING,
    int: hikari.OptionType.INTEGER,
    float: hikari.OptionType.FLOAT,
    bool: hikari.OptionType.BOOLEAN,
    hikari.User: hikari.OptionType.USER,
    hikari.Member: hikari.OptionType.USER,
    hikari.GuildChannel: hikari.OptionType.CHANNEL,
    hikari.Role: hikari.OptionType.ROLE,
    hikari.Attachment: hikari.OptionType.ATTACHMENT,
}

# Parameter names that are never options
_SKIP_NAMES = frozenset({"ctx", "self", "cls"})


def _extract_options(
    func: Callable[..., Any],
    descriptions: dict[str, str] | None = None,
) -> tuple[OptionDescriptor, ...]:
    """Extract option descriptors from a function's signature."""
    sig = inspect.signature(func)
    options: list[OptionDescriptor] = []
    descriptions = descriptions or {}

    for name, param in sig.parameters.items():
        if name in _SKIP_NAMES:
            continue
        if param.annotation is inspect.Parameter.empty:
            continue

        from sosad.di.markers import _InjectMarker

        if isinstance(param.default, _InjectMarker):
            continue

        option_type = _TYPE_MAP.get(param.annotation)
        if option_type is None:
            continue

        required = param.default is inspect.Parameter.empty
        desc = descriptions.get(name, name.replace("_", " ").title())
        options.append(
            OptionDescriptor(
                name=name,
                description=desc,
                type=option_type,
                required=required,
            )
        )

    return tuple(options)


def slash_command(
    name: str,
    description: str,
    *,
    scopes: Sequence[hikari.Snowflake | str] = ("global",),
    default_member_permissions: hikari.Permissions | None = None,
    is_dm_only: bool = False,
    is_guild_only: bool = False,
    nsfw: bool = False,
    option_descriptions: dict[str, str] | None = None,
) -> Callable[[Callable[..., Any]], SlashCommandMeta]:
    """Decorator that marks a function as a slash command.

    Usage::

        @sosad.slash_command("ping", "Check bot latency")
        async def ping(ctx: InteractionContext) -> None:
            await ctx.respond().content("Pong!").send()
    """

    def decorator(func: Callable[..., Any]) -> SlashCommandMeta:
        options = _extract_options(func, option_descriptions)
        meta = SlashCommandMeta(
            name=name,
            description=description,
            handler=func,
            options=options,
            scopes=tuple(scopes),
            default_member_permissions=default_member_permissions,
            is_dm_only=is_dm_only,
            is_guild_only=is_guild_only,
            nsfw=nsfw,
        )
        register_command(meta)
        return meta

    return decorator


def sub_command(
    group: str,
    name: str,
    description: str,
    *,
    parent_scopes: Sequence[hikari.Snowflake | str] | None = None,
    option_descriptions: dict[str, str] | None = None,
) -> Callable[[Callable[..., Any]], SubCommandMeta]:
    """Decorator for a subcommand within a group."""

    def decorator(func: Callable[..., Any]) -> SubCommandMeta:
        options = _extract_options(func, option_descriptions)
        meta = SubCommandMeta(
            group=group,
            name=name,
            description=description,
            handler=func,
            options=options,
            parent_scopes=tuple(parent_scopes) if parent_scopes else None,
        )
        register_command(meta)
        return meta

    return decorator


def command_group(
    name: str,
    description: str,
    *,
    scopes: Sequence[hikari.Snowflake | str] = ("global",),
    default_member_permissions: hikari.Permissions | None = None,
) -> Callable[[Callable[..., Any]], CommandGroupMeta]:
    """Decorator for a command group."""

    def decorator(func: Callable[..., Any]) -> CommandGroupMeta:
        meta = CommandGroupMeta(
            name=name,
            description=description,
            scopes=tuple(scopes),
            default_member_permissions=default_member_permissions,
        )
        register_command(meta)
        return meta

    return decorator


__all__ = ["command_group", "slash_command", "sub_command"]
