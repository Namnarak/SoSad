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

    async def sync(self) -> SyncResult:
        """Sync global commands to Discord (may take ~1 hour to propagate)."""
        result = SyncResult()
        local_builders = self._registry.build_hikari_commands()

        try:
            synced = await self._rest.set_application_commands(
                self._app_id,
                commands=local_builders,
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
        local_builders = self._registry.build_hikari_commands()

        try:
            synced = await self._rest.set_application_commands(
                self._app_id,
                commands=local_builders,
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
