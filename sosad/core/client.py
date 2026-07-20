"""The main SoSad Gateway client. Wraps hikari.GatewayBot via composition."""

from __future__ import annotations

import logging
from typing import Any

import hikari

from sosad._meta import __version__
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
        banner: str = "so sad",
        auto_discover_plugins: bool = True,
        sync_commands: bool = True,
        **kwargs: Any,
    ) -> None:
        self._intents = intents
        super().__init__(
            token=token,
            logs=logs,
            banner=banner,
            auto_discover_plugins=auto_discover_plugins,
            sync_commands=sync_commands,
            **kwargs,
        )
        self._bot: hikari.GatewayBot | None = None

    @property
    def bot(self) -> hikari.GatewayBot:
        if self._bot is None:
            raise RuntimeError("Bot has not been started yet")
        return self._bot

    @property
    def rest(self) -> hikari.api.RESTProvider:
        return self.bot.rest

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

        @self._bot.listen(hikari.StartedEvent)
        async def on_started(event: hikari.StartedEvent) -> None:
            logger.info("SoSad connected as %s", self.bot.get_me())

        @self._bot.listen(hikari.InteractionCreateEvent)
        async def on_interaction(event: hikari.InteractionCreateEvent) -> None:
            await router.handle_interaction(event)

    def _attach_event_dispatcher(self) -> None:
        if self._bot is None:
            return
        try:
            self._event_dispatcher.attach(self._bot)
        except Exception:
            logger.exception("Failed to attach event dispatcher")

    async def close(self) -> None:
        logger.info("SoSad shutting down...")
        if self._bot is not None:
            await self._bot.close()


__all__ = ["Client"]
