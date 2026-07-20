"""Command tree, resolution, and diff logic."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import hikari

from sosad.commands.models import (
    CommandGroupMeta,
    SlashCommandMeta,
    SubCommandMeta,
)

logger = logging.getLogger("sosad.commands")


class CommandRegistry:
    """In-memory command tree. Supports resolution and sync building.

    Usage::

        registry = CommandRegistry()
        registry.add(slash_meta)
        handler = registry.resolve(interaction)
    """

    def __init__(self) -> None:
        self._commands: dict[str, SlashCommandMeta] = {}
        self._groups: dict[str, CommandGroupMeta] = {}
        self._group_subs: dict[str, dict[str, SubCommandMeta]] = {}

    def add(self, meta: SlashCommandMeta | CommandGroupMeta | SubCommandMeta) -> None:
        """Add command metadata to the registry."""
        if isinstance(meta, SlashCommandMeta):
            self._commands[meta.name] = meta
            logger.debug("Registered slash command: %s", meta.name)
        elif isinstance(meta, CommandGroupMeta):
            self._groups[meta.name] = meta
            logger.debug("Registered command group: %s", meta.name)
        elif isinstance(meta, SubCommandMeta):
            if meta.group not in self._group_subs:
                self._group_subs[meta.group] = {}
            self._group_subs[meta.group][meta.name] = meta
            logger.debug("Registered subcommand: %s %s", meta.group, meta.name)

    def remove(self, name: str) -> bool:
        """Remove a top-level command by name. Returns True if found."""
        if name in self._commands:
            del self._commands[name]
            return True
        if name in self._groups:
            del self._groups[name]
            self._group_subs.pop(name, None)
            return True
        return False

    def resolve(
        self,
        interaction: hikari.CommandInteraction,
    ) -> SlashCommandMeta | SubCommandMeta | None:
        """Given an interaction, find the correct handler."""
        command_name = interaction.command_name
        options = interaction.options or []

        for opt in options:
            if opt.type == hikari.OptionType.SUB_COMMAND:
                sub_name = opt.name
                group_subs = self._group_subs.get(command_name, {})
                if sub_name in group_subs:
                    return group_subs[sub_name]

        if command_name in self._commands:
            return self._commands[command_name]

        return None

    def build_hikari_commands(self) -> list[hikari.SnowflakeBasedJSONBuilder[Any]]:
        """Convert internal metadata to Hikari command builders for API sync."""
        builders: list[hikari.SnowflakeBasedJSONBuilder[Any]] = []

        for meta in self._commands.values():
            builder = hikari.api.CommandBuilder()
            builder.name = meta.name
            builder.description = meta.description
            builder.type = hikari.CommandType.SLASH
            if meta.default_member_permissions is not None:
                builder.default_member_permissions = meta.default_member_permissions
            if meta.is_dm_only:
                builder.integration_types = [
                    hikari.ApplicationIntegrationType.USER_INSTALL,
                ]
                builder.contexts = [
                    hikari.InteractionContextType.BOT_DM,
                    hikari.InteractionContextType.PRIVATE_CHANNEL,
                ]

            options: list[dict[str, Any]] = []
            for opt in meta.options:
                opt_data: dict[str, Any] = {
                    "type": opt.type.value,
                    "name": opt.name,
                    "description": opt.description,
                    "required": opt.required,
                }
                if opt.choices:
                    opt_data["choices"] = [
                        {"name": c[0], "value": c[1]} for c in opt.choices
                    ]
                options.append(opt_data)
            builder.options = options
            builders.append(builder)

        for group_name, group_meta in self._groups.items():
            builder = hikari.api.CommandBuilder()
            builder.name = group_name
            builder.description = group_meta.description
            builder.type = hikari.CommandType.SLASH
            if group_meta.default_member_permissions is not None:
                builder.default_member_permissions = (
                    group_meta.default_member_permissions
                )

            subs = self._group_subs.get(group_name, {})
            sub_options: list[dict[str, Any]] = []
            for sub_name, sub_meta in subs.items():
                sub_data: dict[str, Any] = {
                    "type": hikari.OptionType.SUB_COMMAND.value,
                    "name": sub_name,
                    "description": sub_meta.description,
                    "options": [],
                }
                for opt in sub_meta.options:
                    opt_data = {
                        "type": opt.type.value,
                        "name": opt.name,
                        "description": opt.description,
                        "required": opt.required,
                    }
                    sub_data["options"].append(opt_data)
                sub_options.append(sub_data)
            builder.options = sub_options
            builders.append(builder)

        return builders

    def compute_hash(self) -> str:
        """Compute a hash of all registered commands for sync diffing."""
        data: list[dict[str, Any]] = []
        for meta in self._commands.values():
            data.append({
                "name": meta.name,
                "description": meta.description,
                "options": [
                    {"name": o.name, "description": o.description, "type": o.type.value}
                    for o in meta.options
                ],
            })
        for name, meta in self._groups.items():
            data.append({
                "name": name,
                "description": meta.description,
                "subcommands": [
                    {"name": s.name, "description": s.description}
                    for s in meta.subcommands
                ],
            })
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]

    def clear(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()
        self._groups.clear()
        self._group_subs.clear()

    @property
    def command_count(self) -> int:
        """Number of registered commands (including subcommands)."""
        count = len(self._commands) + len(self._groups)
        for subs in self._group_subs.values():
            count += len(subs)
        return count

    @property
    def command_names(self) -> list[str]:
        """List of all registered command names."""
        names = list(self._commands.keys())
        names.extend(self._groups.keys())
        return names


__all__ = ["CommandRegistry"]
