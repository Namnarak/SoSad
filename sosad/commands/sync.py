"""Syncs the local command registry to Discord."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import hikari

from sosad.commands.registry import CommandRegistry

logger = logging.getLogger("sosad.sync")


@dataclass(frozen=True)
class SyncResult:
    """Result of a command sync operation."""

    commands_synced: int = 0
    errors: list[str] = field(default_factory=list)


class CommandSyncer:
    """Syncs the local command registry to Discord.

    Uses set_application_commands() for reliable bulk sync.

    Usage::

        syncer = CommandSyncer(rest, registry, app_id)
        result = await syncer.sync()
    """

    def __init__(
        self,
        rest: hikari.api.RESTProvider,
        registry: CommandRegistry,
        app_id: hikari.Snowflake,
    ) -> None:
        self._rest = rest
        self._registry = registry
        self._app_id = app_id

    def _build_command(self, cmd: dict[str, Any]) -> Any:
        """Convert a command dict to a Hikari SlashCommandBuilder."""
        builder = self._rest.slash_command_builder(
            cmd["name"],
            cmd["description"],
        )
        if "options" in cmd:
            for opt in cmd["options"]:
                option_type = hikari.OptionType(opt["type"])
                if option_type == hikari.OptionType.SUB_COMMAND:
                    sub = builder.sub_option(opt["name"], opt["description"])
                    if "options" in opt:
                        for sub_opt in opt["options"]:
                            sub.add_option(hikari.CommandOption(
                                type=hikari.OptionType(sub_opt["type"]),
                                name=sub_opt["name"],
                                description=sub_opt["description"],
                                is_required=sub_opt.get("required", False),
                            ))
                else:
                    builder.add_option(hikari.CommandOption(
                        type=option_type,
                        name=opt["name"],
                        description=opt["description"],
                        is_required=opt.get("required", False),
                    ))
        return builder

    async def sync(self) -> SyncResult:
        """Sync global commands to Discord (may take ~1 hour to propagate)."""
        result = SyncResult()
        cmd_dicts = self._registry.build_hikari_commands()
        builders = [self._build_command(cmd) for cmd in cmd_dicts]

        try:
            synced = await self._rest.set_application_commands(
                self._app_id,
                commands=builders,
            )
            result.commands_synced = len(synced)
            logger.info("Global sync: %d commands synced", result.commands_synced)
        except Exception as exc:
            result.errors.append(f"Failed to sync global commands: {exc}")
            logger.exception("Global command sync failed")

        return result

    async def sync_guild(self, guild_id: hikari.Snowflake) -> SyncResult:
        """Sync commands to a specific guild (instant, no propagation delay)."""
        result = SyncResult()
        cmd_dicts = self._registry.build_hikari_commands()
        builders = [self._build_command(cmd) for cmd in cmd_dicts]

        try:
            synced = await self._rest.set_application_commands(
                self._app_id,
                commands=builders,
                guild=guild_id,
            )
            result.commands_synced = len(synced)
            logger.info(
                "Guild sync (%s): %d commands synced",
                guild_id,
                result.commands_synced,
            )
        except Exception as exc:
            result.errors.append(f"Failed to sync guild commands: {exc}")
            logger.exception("Guild command sync failed for %s", guild_id)

        return result


__all__ = ["CommandSyncer", "SyncResult"]
