"""The main SoSad Gateway client. Wraps hikari.GatewayBot via composition."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import hikari

from sosad._meta import __version__
from sosad.commands.prefix import PrefixRegistry, get_prefix_registry, handle_prefix_message
from sosad.core.base_client import BaseClient

logger = logging.getLogger("sosad")


class Client(BaseClient):
    """SoSad Gateway client. Wraps hikari.GatewayBot via composition.

    Usage::

        bot = sosad.Client(token="...", intents=hikari.Intents.ALL_UNPRIVILEGED)

        @sosad.slash_command("ping", "Check bot latency")
        async def ping(ctx: sosad.InteractionContext) -> None:
            await ctx.respond("Pong!")

        bot.run()
    """

    def __init__(
        self,
        *,
        token: str,
        intents: hikari.Intents,
        logs: str | int = "INFO",
        banner: str | None = None,
        auto_discover_plugins: bool = True,
        sync_commands: bool = True,
        **kwargs: Any,
    ) -> None:
        self._intents = intents
        self._prefix: str = "!"
        self._prefix_registry: PrefixRegistry | None = None
        self._pending_listeners: list[tuple[type[hikari.Event], Callable[..., Any]]] = []
        self._sync_commands = sync_commands
        self._guild_id: hikari.Snowflake | None = None
        super().__init__(
            token=token,
            logs=logs,
            banner=banner,
            auto_discover_plugins=auto_discover_plugins,
            **kwargs,
        )
        self._bot: hikari.GatewayBot | None = None

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int | str | hikari.Snowflake | None) -> None:
        self._guild_id = hikari.Snowflake(value) if value is not None else None

    @property
    def bot(self) -> hikari.GatewayBot:
        if self._bot is None:
            raise RuntimeError("Bot has not been started yet")
        return self._bot

    @property
    def rest(self) -> hikari.api.RESTProvider:
        return self.bot.rest

    @property
    def shard_count(self) -> int:
        """Number of shards this bot is connected to."""
        return getattr(self._bot, "shard_count", 1) if self._bot else 1

    @property
    def shard_ids(self) -> list[int]:
        """IDs of shards this bot owns."""
        shard = getattr(self._bot, "shard", None)
        if shard is not None:
            return [shard.id]
        return [0]

    @property
    def is_shard_aware(self) -> bool:
        """Whether the bot supports sharding."""
        return hasattr(self._bot, "shard_count")

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        self._prefix = value

    @property
    def prefix_registry(self) -> PrefixRegistry:
        if self._prefix_registry is None:
            self._prefix_registry = get_prefix_registry()
        return self._prefix_registry

    def listen(
        self,
        event_type: type[hikari.Event],
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to listen for events. Works before bot.run().

        Usage::

            @bot.listen(hikari.InteractionCreateEvent)
            async def on_interaction(event):
                ...
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._pending_listeners.append((event_type, func))
            return func
        return decorator

    def run(self) -> None:
        """Start the bot (blocking)."""
        self._bot = hikari.GatewayBot(
            token=self._token,
            intents=self._intents,
            logs=self._logs,
            banner=self._banner,
            **self._hikari_kwargs,
        )

        self._init_registry_and_router()
        self._load_pending_plugins()
        self._setup_listeners()
        self._auto_discover_plugins()
        self._attach_event_dispatcher()
        self._start_tasks()

        cmd_count = self._registry.command_count if self._registry else 0
        logger.info("SoSad v%s (Gateway) starting with %d commands...", __version__, cmd_count)
        self._bot.run()

    def _setup_listeners(self) -> None:
        if self._bot is None or self._router is None:
            return

        router = self._router
        client = self

        @self._bot.listen(hikari.StartedEvent)
        async def on_started(event: hikari.StartedEvent) -> None:
            logger.info("SoSad connected as %s", self.bot.get_me())
            if client._sync_commands:
                await client._sync_all_commands()

        @self._bot.listen(hikari.InteractionCreateEvent)
        async def on_interaction(event: hikari.InteractionCreateEvent) -> None:
            await router.handle_interaction(event)

        @self._bot.listen(hikari.GuildMessageCreateEvent)
        async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
            await handle_prefix_message(
                event.message,
                client,
                prefix=client._prefix,
                registry=client._prefix_registry,
            )

        for event_type, handler in self._pending_listeners:
            self._bot.listen(event_type)(handler)

    def _attach_event_dispatcher(self) -> None:
        if self._bot is None:
            return
        try:
            self._event_dispatcher.attach(self._bot)
        except Exception:
            logger.exception("Failed to attach event dispatcher")

    async def _sync_all_commands(self) -> None:
        """Sync all commands — global + guild if set."""
        if self._bot is None or self._registry is None:
            return
        from sosad.commands.sync import CommandSyncer
        me = self._bot.get_me()
        if me is None:
            return
        syncer = CommandSyncer(self._bot.rest, self._registry, me.id)

        # Always sync global commands
        result = await syncer.sync()
        logger.info(
            "Global sync: %d created, %d updated, %d deleted",
            result.created, result.updated, result.deleted,
        )

        # Also sync guild-specific commands if guild_id is set
        if self._guild_id is not None:
            guild_result = await syncer.sync_guild(self._guild_id)
            logger.info(
                "Guild sync (%s): %d created, %d updated, %d deleted",
                self._guild_id,
                guild_result.created, guild_result.updated, guild_result.deleted,
            )

    async def close(self) -> None:
        logger.info("SoSad shutting down...")
        if self._bot is not None:
            await self._bot.close()


__all__ = ["Client"]
