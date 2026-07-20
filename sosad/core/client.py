"""The main SoSad client. Wraps hikari.GatewayBot via composition."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import hikari

from sosad._meta import __version__
from sosad.commands.executor import execute_command
from sosad.commands.registration import get_registry
from sosad.commands.registry import CommandRegistry
from sosad.commands.router import CommandRouter
from sosad.context.context import InteractionContext
from sosad.core.app import App
from sosad.di.container import Container
from sosad.di.scopes import ScopeManager
from sosad.errors.handler import ErrorPipeline
from sosad.middleware.builtins import logging_middleware
from sosad.middleware.registry import MiddlewareStack
from sosad.middleware.types import HandlerFunc

logger = logging.getLogger("sosad")


class Client:
    """The main SoSad client. Wraps hikari.GatewayBot via composition.

    Usage::

        bot = sosad.Client(token="...", intents=hikari.Intents.ALL_UNPRIVILEGED)

        # Or use 'app' alias:
        app = sosad.Client(token="...", intents=hikari.Intents.ALL_UNPRIVILEGED)
    """

    def __init__(
        self,
        *,
        token: str,
        intents: hikari.Intents,
        logs: str | int = "INFO",
        banner: str = "so sad",
        auto_discover_plugins: bool = True,
        **kwargs: Any,
    ) -> None:
        self._token = token
        self._intents = intents
        self._logs = logs
        self._banner = banner
        self._auto_discover = auto_discover_plugins
        self._hikari_kwargs = kwargs
        self._app = App()
        self._bot: hikari.GatewayBot | None = None
        self._container = Container()
        self._error_pipeline = ErrorPipeline()
        self._middleware_stack = MiddlewareStack()
        self._middleware_stack.add(logging_middleware)
        self._registry: CommandRegistry | None = None
        self._router: CommandRouter | None = None

    @property
    def app(self) -> App:
        return self._app

    @property
    def bot(self) -> hikari.GatewayBot:
        if self._bot is None:
            raise RuntimeError("Bot has not been started yet")
        return self._bot

    @property
    def rest(self) -> hikari.api.RESTProvider:
        return self.bot.rest

    @property
    def container(self) -> Container:
        return self._container

    @property
    def error_pipeline(self) -> ErrorPipeline:
        return self._error_pipeline

    def use(self, *middlewares: Any) -> None:
        for mw in middlewares:
            self._middleware_stack.add(mw)

    def on_error(self, error_type: type[Exception], handler: Any = None) -> Any:
        if handler is not None:
            self._error_pipeline.on(error_type, handler)
            return handler

        def decorator(fn: Any) -> Any:
            self._error_pipeline.on(error_type, fn)
            return fn

        return decorator

    def load_plugins(self, *paths: str | Path) -> None:
        """Load plugins from directories."""
        from sosad.plugins.manager import PluginManager
        manager = PluginManager(self)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.load_all(*paths))
        except RuntimeError:
            # No event loop running — store for later
            self._pending_plugins = list(paths)  # type: ignore[attr-defined]

    def _auto_discover_plugins(self) -> None:
        """Auto-discover plugins from plugins/ directory."""
        plugins_dir = Path("plugins")
        if plugins_dir.is_dir() and self._auto_discover:
            logger.info("Auto-discovering plugins from plugins/")
            self.load_plugins(plugins_dir)

    def _build_pipeline(self) -> HandlerFunc:
        stack = MiddlewareStack()
        for mw in self._middleware_stack._middlewares:
            stack.add(mw)

        error_pipeline = self._error_pipeline

        async def error_handler_middleware(
            ctx: InteractionContext,
            next_fn: HandlerFunc,
            scope: ScopeManager,
        ) -> None:
            try:
                await next_fn(ctx, scope)
            except Exception as exc:
                await error_pipeline.handle(exc, ctx)

        stack.add(error_handler_middleware)

        registry = self._registry
        container = self._container
        error_pipe = self._error_pipeline

        async def final_handler(
            ctx: InteractionContext,
            scope: ScopeManager,
        ) -> None:
            if registry is None:
                return
            meta = registry.resolve(ctx.interaction)
            if meta is None:
                return
            try:
                await execute_command(meta, ctx, scope, container)
            except Exception as exc:
                await error_pipe.handle(exc, ctx)

        stack.set_handler(final_handler)
        return stack.build()

    def run(self) -> None:
        """Start the bot (blocking)."""
        self._bot = hikari.GatewayBot(
            token=self._token,
            intents=self._intents,
            logs=self._logs,
            banner=self._banner,
            **self._hikari_kwargs,
        )

        self._registry = get_registry()
        pipeline = self._build_pipeline()
        self._router = CommandRouter(self._registry, self, pipeline)

        self._setup_listeners()
        self._auto_discover_plugins()
        cmd_count = self._registry.command_count
        logger.info("SoSad v%s starting with %d commands...", __version__, cmd_count)
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

    async def close(self) -> None:
        logger.info("SoSad shutting down...")
        if self._bot is not None:
            await self._bot.close()


__all__ = ["Client"]
