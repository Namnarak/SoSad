"""REST-only bot client. Wraps hikari.RESTBot or runs a custom aiohttp server."""

from __future__ import annotations

import logging
from typing import Any, Literal

import hikari

from sosad._meta import __version__
from sosad.core.base_client import BaseClient

logger = logging.getLogger("sosad.rest")

ServerMode = Literal["hikari", "custom"]


class RESTClient(BaseClient):
    """SoSad REST-only client.

    Runs an HTTP server that receives interactions from Discord via POST requests.
    No WebSocket connection needed — lightweight and serverless-friendly.

    Two server backends:
    - ``"hikari"`` (default): uses ``hikari.RESTBot`` — full-featured, automatic
    - ``"custom"``: uses aiohttp + hikari's ``InteractionServer`` — more control

    Usage (hikari backend)::

        bot = sosad.RESTClient(
            token="...",
            public_key="...",
        )
        bot.run(host="0.0.0.0", port=8080)

    Usage (custom aiohttp backend)::

        bot = sosad.RESTClient(
            token="...",
            public_key="...",
            server="custom",
        )
        bot.run(host="0.0.0.0", port=8080)
    """

    def __init__(
        self,
        *,
        token: str,
        public_key: str | bytes | None = None,
        server: ServerMode = "hikari",
        logs: str | int = "INFO",
        banner: str = "so sad",
        auto_discover_plugins: bool = True,
        sync_commands: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            token=token,
            logs=logs,
            banner=banner,
            auto_discover_plugins=auto_discover_plugins,
            **kwargs,
        )
        self._public_key = public_key
        self._server_mode = server
        self._bot: hikari.RESTBot | None = None
        self._custom_server: Any = None
        self._custom_rest: Any = None
        self._sync_commands = sync_commands

    @property
    def is_rest(self) -> bool:
        return True

    @property
    def bot(self) -> hikari.RESTBot | None:
        return self._bot

    @property
    def rest(self) -> hikari.api.RESTClient:
        if self._bot is not None:
            return self._bot.rest
        if self._custom_rest is not None:
            return self._custom_rest
        raise RuntimeError("RESTClient has not been started yet")

    def run(
        self,
        *,
        host: str | list[str] | None = None,
        port: int | None = None,
        path: str | None = None,
        ssl_context: Any = None,
        backlog: int = 128,
        shutdown_timeout: float = 60.0,
        socket: Any = None,
        reuse_address: bool | None = None,
        reuse_port: bool | None = None,
        check_for_updates: bool = True,
    ) -> None:
        """Start the REST bot (blocking).

        Parameters
        ----------
        host : str or list of str, optional
            Host(s) to bind to. Defaults to ``"0.0.0.0"``.
        port : int, optional
            Port to bind to. Defaults to ``8080``.
        path : str, optional
            URL path for interactions. Defaults to ``"/"`` (hikari backend)
            or ``"/interactions"`` (custom backend).
        ssl_context : ssl.SSLContext, optional
            SSL context for HTTPS. Required for production Discord integration.
        """
        self._auto_discover_plugins()
        self._load_pending_plugins()
        self._init_registry_and_router()
        self._start_tasks()

        if self._server_mode == "custom":
            self._run_custom_server(
                host=host or "0.0.0.0",
                port=port or 8080,
                path=path or "/interactions",
                ssl_context=ssl_context,
                backlog=backlog,
                shutdown_timeout=shutdown_timeout,
                socket=socket,
                reuse_address=reuse_address,
                reuse_port=reuse_port,
            )
        else:
            self._run_hikari_server(
                host=host,
                port=port,
                path=path,
                ssl_context=ssl_context,
                backlog=backlog,
                shutdown_timeout=shutdown_timeout,
                socket=socket,
                reuse_address=reuse_address,
                reuse_port=reuse_port,
                check_for_updates=check_for_updates,
            )

    def _run_hikari_server(
        self,
        host: str | list[str] | None = None,
        port: int | None = None,
        path: str | None = None,
        ssl_context: Any = None,
        backlog: int = 128,
        shutdown_timeout: float = 60.0,
        socket: Any = None,
        reuse_address: bool | None = None,
        reuse_port: bool | None = None,
        check_for_updates: bool = True,
    ) -> None:
        self._bot = hikari.RESTBot(
            token=self._token,
            public_key=self._public_key,
            logs=self._logs,
            banner=self._banner,
            **self._hikari_kwargs,
        )

        if self._router is not None:
            self._bot.set_listener(
                hikari.CommandInteraction,
                self._handle_hikari_interaction,
            )
            self._bot.set_listener(
                hikari.ComponentInteraction,
                self._handle_hikari_component,
            )
            self._bot.set_listener(
                hikari.ModalInteraction,
                self._handle_hikari_modal,
            )
            self._bot.set_listener(
                hikari.AutocompleteInteraction,
                self._handle_hikari_autocomplete,
            )
        if self._sync_commands:
            self._bot.add_startup_callback(self._sync_all_commands)

        cmd_count = self._registry.command_count if self._registry else 0
        logger.info("SoSad v%s (REST/hikari) starting with %d commands...", __version__, cmd_count)

        self._bot.run(
            host=host,
            port=port,
            path=path,
            backlog=backlog,
            shutdown_timeout=shutdown_timeout,
            socket=socket,
            reuse_address=reuse_address,
            reuse_port=reuse_port,
            ssl_context=ssl_context,
            check_for_updates=check_for_updates,
        )

    def _run_custom_server(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        path: str = "/interactions",
        ssl_context: Any = None,
        backlog: int = 128,
        shutdown_timeout: float = 60.0,
        socket: Any = None,
        reuse_address: bool | None = None,
        reuse_port: bool | None = None,
    ) -> None:
        """Run custom aiohttp server with hikari's InteractionServer."""
        try:
            from aiohttp import web
        except ImportError as exc:
            raise ImportError(
                "aiohttp is required for custom server mode. "
                "Install it with: pip install aiohttp"
            ) from exc

        try:
            rest_client = hikari.impl.RESTClientImpl(
                token=self._token,
                entity_factory=hikari.impl.entity_factory.EntityFactoryImpl(
                    app=None,
                ),
                executor=None,
                http_settings=hikari.impl.config.HTTPSettings(),
                max_rate_limit=300.0,
                max_retries=3,
            )

            entity_factory = hikari.impl.entity_factory.EntityFactoryImpl(
                app=rest_client,
            )

            self._custom_rest = rest_client

            server = hikari.impl.interaction_server.InteractionServer(
                entity_factory=entity_factory,
                rest_client=rest_client,
                public_key=self._public_key,
            )
        except AttributeError as exc:
            raise ImportError(
                f"hikari internal classes not available: {exc}. "
                "Try using server='hikari' mode instead, or upgrade hikari."
            ) from exc

        if self._router is not None:
            server.set_listener(
                hikari.CommandInteraction,
                self._handle_hikari_interaction,
            )
            server.set_listener(
                hikari.ComponentInteraction,
                self._handle_hikari_component,
            )
            server.set_listener(
                hikari.ModalInteraction,
                self._handle_hikari_modal,
            )
            server.set_listener(
                hikari.AutocompleteInteraction,
                self._handle_hikari_autocomplete,
            )

        self._custom_server = server

        async def handle_post(request: web.Request) -> web.Response:
            body = await request.read()
            signature = request.headers.get("X-Signature-Ed25519", "").encode()
            timestamp = request.headers.get("X-Signature-Timestamp", "").encode()

            response = await server.on_interaction(body, signature, timestamp)

            return web.Response(
                status=response.status,
                body=response.body,
                headers=dict(response.headers) if response.headers else {},
                content_type="application/json",
            )

        async def handle_get(request: web.Request) -> web.Response:
            return web.Response(text="SoSad REST Bot is running.")

        app = web.Application()

        async def on_startup(_: web.Application) -> None:
            rest_client.start()
            if self._sync_commands and self._registry is not None:
                from sosad.commands.sync import CommandSyncer

                me = await rest_client.fetch_my_user()
                result = await CommandSyncer(rest_client, self._registry, me.id).sync()
                for error in result.errors:
                    logger.error(error)

        async def on_cleanup(_: web.Application) -> None:
            rest_client.close()

        app.on_startup.append(on_startup)
        app.on_cleanup.append(on_cleanup)
        app.router.add_post(path, handle_post)
        app.router.add_get("/", handle_get)

        cmd_count = self._registry.command_count if self._registry else 0
        logger.info("SoSad v%s (REST/custom) starting with %d commands...", __version__, cmd_count)

        web.run_app(
            app,
            host=host,
            port=port,
            path=path,
            backlog=backlog,
            shutdown_timeout=shutdown_timeout,
            reuse_address=reuse_address,
            reuse_port=reuse_port,
            ssl_context=ssl_context,
        )

    async def _handle_hikari_interaction(
        self,
        interaction: hikari.CommandInteraction,
    ) -> None:
        """Handle a command interaction from RESTBot or InteractionServer."""
        if self._router is None:
            return
        await self._router.handle_interaction_event(interaction)
        return None

    async def _sync_all_commands(self, bot: hikari.RESTBot) -> None:
        """Synchronize scoped global commands once the REST client is open."""
        if self._registry is None:
            return
        from sosad.commands.sync import CommandSyncer

        me = await bot.rest.fetch_my_user()
        result = await CommandSyncer(bot.rest, self._registry, me.id).sync()
        for error in result.errors:
            logger.error(error)

    async def _handle_hikari_component(
        self,
        interaction: hikari.ComponentInteraction,
    ) -> None:
        if self._router is None:
            return
        await self._router.handle_component_interaction(interaction)

    async def _handle_hikari_modal(
        self,
        interaction: hikari.ModalInteraction,
    ) -> None:
        if self._router is None:
            return
        await self._router.handle_modal_interaction(interaction)

    async def _handle_hikari_autocomplete(
        self,
        interaction: hikari.AutocompleteInteraction,
    ) -> None:
        if self._router is None:
            return
        await self._router.handle_autocomplete_interaction(interaction)

    async def close(self) -> None:
        logger.info("SoSad REST shutting down...")
        if self._bot is not None:
            await self._bot.close()


__all__ = ["RESTClient", "ServerMode"]
