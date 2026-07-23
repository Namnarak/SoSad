"""Metadata dataclasses for commands."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import hikari

if TYPE_CHECKING:
    from sosad.checks.base import CheckFunc
    from sosad.cooldowns.buckets import CooldownConfig


@dataclass(frozen=True, slots=True)
class OptionDescriptor:
    """Describes a single slash command option."""

    name: str
    description: str
    type: hikari.OptionType
    required: bool = True
    choices: Sequence[tuple[str, str | int | float]] | None = None
    autocomplete: bool = False


@dataclass(frozen=True, slots=True)
class SlashCommandMeta:
    """Metadata collected by @slash_command decorator."""

    name: str
    description: str
    handler: Callable[..., Any]
    options: tuple[OptionDescriptor, ...] = ()
    scopes: tuple[hikari.Snowflake | str, ...] = ("global",)
    default_member_permissions: hikari.Permissions | None = None
    is_dm_only: bool = False
    nsfw: bool = False
    is_guild_only: bool = False
    checks: tuple[CheckFunc, ...] = ()
    cooldown: CooldownConfig | None = None

    def __post_init__(self) -> None:
        if not self.checks:
            object.__setattr__(
                self,
                "checks",
                tuple(getattr(self.handler, "__sosad_checks__", ())),
            )
        if self.cooldown is None:
            object.__setattr__(
                self,
                "cooldown",
                getattr(self.handler, "__sosad_cooldown__", None),
            )


@dataclass(frozen=True, slots=True)
class SubCommandMeta:
    """Metadata collected by @sub_command decorator."""

    group: str
    name: str
    description: str
    handler: Callable[..., Any]
    options: tuple[OptionDescriptor, ...] = ()
    parent_scopes: tuple[hikari.Snowflake | str, ...] | None = None
    checks: tuple[CheckFunc, ...] = ()
    cooldown: CooldownConfig | None = None

    def __post_init__(self) -> None:
        if not self.checks:
            object.__setattr__(
                self,
                "checks",
                tuple(getattr(self.handler, "__sosad_checks__", ())),
            )
        if self.cooldown is None:
            object.__setattr__(
                self,
                "cooldown",
                getattr(self.handler, "__sosad_cooldown__", None),
            )


@dataclass(frozen=True, slots=True)
class CommandGroupMeta:
    """Metadata collected by @command_group decorator."""

    name: str
    description: str
    subcommands: tuple[SubCommandMeta, ...] = ()
    scopes: tuple[hikari.Snowflake | str, ...] = ("global",)
    default_member_permissions: hikari.Permissions | None = None


__all__ = [
    "CommandGroupMeta",
    "OptionDescriptor",
    "SlashCommandMeta",
    "SubCommandMeta",
]
