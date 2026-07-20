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

    created: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    errors: list[str] = field(default_factory=list)


class CommandSyncer:
    """Syncs the local command registry to Discord.

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

    async def sync(self, *, delete_orphans: bool = True) -> SyncResult:
        """Sync commands to Discord.

        1. Fetch current commands from Discord
        2. Diff against local registry
        3. Batch create/update/delete via REST API
        """
        result = SyncResult()
        local_builders = self._registry.build_hikari_commands()

        try:
            remote_commands = await self._rest.fetch_application_commands(self._app_id)
        except Exception as exc:
            result.errors.append(f"Failed to fetch commands: {exc}")
            return result

        remote_map = {cmd.name: cmd for cmd in remote_commands}
        local_map = {getattr(b, "name", "unknown"): b for b in local_builders}

        # Create or update
        for name, builder in local_map.items():
            if name in remote_map:
                remote = remote_map[name]
                if self._needs_update(builder, remote):
                    try:
                        await self._rest.edit_application_command(
                            self._app_id,
                            remote.id,
                            builder=builder,
                        )
                        result.updated += 1
                    except Exception as exc:
                        result.errors.append(f"Failed to update {name}: {exc}")
                else:
                    result.unchanged += 1
            else:
                try:
                    await self._rest.create_application_command(
                        self._app_id,
                        builder=builder,
                    )
                    result.created += 1
                except Exception as exc:
                    result.errors.append(f"Failed to create {name}: {exc}")

        # Delete orphans
        if delete_orphans:
            for name, remote in remote_map.items():
                if name not in local_map:
                    try:
                        await self._rest.delete_application_command(
                            self._app_id,
                            remote.id,
                        )
                        result.deleted += 1
                    except Exception as exc:
                        result.errors.append(f"Failed to delete {name}: {exc}")

        logger.info(
            "Command sync: %d created, %d updated, %d deleted, %d unchanged",
            result.created,
            result.updated,
            result.deleted,
            result.unchanged,
        )
        return result

    def _needs_update(self, builder: Any, remote: Any) -> bool:
        """Check if a command needs updating."""
        remote_name = getattr(remote, "name", None)
        builder_name = getattr(builder, "name", None)
        if remote_name != builder_name:
            return True
        remote_desc = getattr(remote, "description", None)
        builder_desc = getattr(builder, "description", None)
        return remote_desc != builder_desc


__all__ = ["CommandSyncer", "SyncResult"]
