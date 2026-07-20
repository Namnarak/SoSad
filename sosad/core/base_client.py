"""Base client with shared logic for both Gateway and REST clients."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from sosad.commands.executor import execute_command
from sosad.commands.registration import get_registry
from sosad.commands.registry import CommandRegistry
from sosad.commands.router import CommandRouter
from sosad.context.context import InteractionContext
from sosad.core.app import App
from sosad.di.container import Container
from sosad.di.scopes import ScopeManager
from sosad.errors.handler import ErrorPipeline
from sosad.events.dispatcher import EventDispatcher
from sosad.middleware.builtins import logging_middleware
from sosad.middleware.registry import MiddlewareStack
from sosad.middleware.types import HandlerFunc, MiddlewareFunc
from sosad.tasks.registry import get_task_registry
from sosad.tasks.scheduler import TaskScheduler

logger = logging.getLogger("sosad")


class BaseClient:
    """Shared client logic for both Gateway and REST modes.

    Handles DI container, middleware pipeline, error handling,
    plugin management, command registration, and task scheduler.
    """

    def __init__(
        self,
        *,
        token: str,
        logs: str | int = "INFO",
        banner: str = "so sad",
        auto_discover_plugins: bool = True,
        **kwargs: Any,
    ) -> None:
        self._token = token
        self._logs = logs
        self._banner = banner
        self._auto_discover = auto_discover_plugins
        self._hikari_kwargs = kwargs
        self._app = App()
        self._container = Container()
        self._error_pipeline = ErrorPipeline()
        self._middleware_stack = MiddlewareStack()
        self._middleware_stack.add(logging_middleware)
        self._registry: CommandRegistry | None = None
        self._router: CommandRouter | None = None
        self._event_dispatcher = EventDispatcher()
        self._pending_plugins: list[Path] = []
        self._scheduler = TaskScheduler()
        self._started_tasks = False

    @property
    def app(self) -> App:
        return self._app

    @property
    def container(self) -> Container:
        return self._container

    @property
    def error_pipeline(self) -> ErrorPipeline:
        return self._error_pipeline

    @property
    def registry(self) -> CommandRegistry | None:
        return self._registry

    @property
    def is_rest(self) -> bool:
        """True for RESTClient, False for Client (Gateway)."""
        return False

    def use(self, *middlewares: MiddlewareFunc | Any) -> None:
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
        from sosad.plugins.manager import PluginManager
        manager = PluginManager(self)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.load_all(*paths))
        except RuntimeError:
            self._pending_plugins = list(paths)

    def _auto_discover_plugins(self) -> None:
        plugins_dir = Path("plugins")
        if plugins_dir.is_dir() and self._auto_discover:
            logger.info("Auto-discovering plugins from plugins/")
            self.load_plugins(plugins_dir)

    def _load_pending_plugins(self) -> None:
        if self._pending_plugins:
            from sosad.plugins.manager import PluginManager
            manager = PluginManager(self)
            import asyncio
            loop = asyncio.get_event_loop()
            for path in self._pending_plugins:
                loop.create_task(manager.load_all(path))

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

    @property
    def scheduler(self) -> TaskScheduler:
        return self._scheduler

    def _discover_tasks(self) -> None:
        """Auto-register tasks from global task registry."""
        for meta in get_task_registry().all.values():
            self._scheduler.register(meta)
            logger.debug("Discovered task: %s", meta.name)

    def _start_tasks(self) -> None:
        if self._started_tasks:
            return
        self._discover_tasks()
        self._scheduler.start_all()
        self._started_tasks = True
        count = self._scheduler.running_count
        logger.info("Started %d background tasks", count)

    def _init_registry_and_router(self) -> None:
        self._registry = get_registry()
        pipeline = self._build_pipeline()
        self._router = CommandRouter(self._registry, self, pipeline)


__all__ = ["BaseClient"]
