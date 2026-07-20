"""discord.py-compatible Bot class — works with both Gateway and REST."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

import hikari

import sosad
from sosad.commands.prefix import PrefixContext, get_prefix_registry
from sosad.compat.context import Context
from sosad.core.base_client import BaseClient
from sosad.core.client import Client
from sosad.core.rest_client import RESTClient

BotMode = Literal["gateway", "rest"]


class Bot:
    """discord.py-compatible Bot that supports both Gateway and REST modes.

    Usage (Gateway)::

        import sosad.compat as discord

        bot = discord.Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            token="TOKEN",
        )

        @bot.command(name="ping")
        async def ping(ctx):
            await ctx.send("Pong!")

        bot.run()

    Usage (REST)::

        import sosad.compat as discord

        bot = discord.Bot(
            mode="rest",
            token="TOKEN",
            public_key="...",
        )

        @bot.command(name="ping")
        async def ping(ctx):
            await ctx.send("Pong!")

        bot.run(host="0.0.0.0", port=8080)
    """

    def __init__(
        self,
        *,
        mode: BotMode = "gateway",
        command_prefix: str = "!",
        intents: hikari.Intents | None = None,
        token: str | None = None,
        public_key: str | bytes | None = None,
        logs: str | int = "INFO",
        banner: str = "so sad",
        auto_discover_plugins: bool = True,
        **kwargs: Any,
    ) -> None:
        self._mode = mode
        self._command_prefix = command_prefix

        if mode == "rest":
            if token is None:
                raise ValueError("token is required for REST mode")
            self._client: BaseClient = RESTClient(
                token=token,
                public_key=public_key,
                logs=logs,
                banner=banner,
                auto_discover_plugins=auto_discover_plugins,
                **kwargs,
            )
        else:
            if intents is None:
                intents = hikari.Intents.ALL_UNPRIVILEGED
            if token is None:
                raise ValueError("token is required")
            self._client = Client(
                token=token,
                intents=intents,
                logs=logs,
                banner=banner,
                auto_discover_plugins=auto_discover_plugins,
                **kwargs,
            )

        self._prefix_commands: dict[str, Callable[..., Any]] = {}
        if hasattr(self._client, "prefix"):
            self._client.prefix = command_prefix

    # ── Client property delegation ──

    @property
    def container(self) -> Any:
        return self._client.container

    @property
    def app(self) -> Any:
        return self._client.app

    @property
    def error_pipeline(self) -> Any:
        return self._client.error_pipeline

    @property
    def registry(self) -> Any:
        return self._client.registry

    @property
    def scheduler(self) -> Any:
        if hasattr(self._client, "scheduler"):
            return self._client.scheduler
        return None

    @property
    def bot(self) -> Any:
        if hasattr(self._client, "bot"):
            return self._client.bot
        return None

    # ── Client method delegation ──

    def use(self, *middlewares: Any) -> None:
        self._client.use(*middlewares)

    def on_error(self, error_type: type[Exception], handler: Any = None) -> Any:
        return self._client.on_error(error_type, handler)

    def load_plugins(self, *paths: Any) -> None:
        self._client.load_plugins(*paths)

    def add_check(self, check: Any) -> None:
        if hasattr(self._client, "add_check"):
            self._client.add_check(check)

    # ── discord.py-compatible API ──

    def command(
        self,
        name: str | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a command (slash or prefix).

        Usage::

            @bot.command(name="ping")
            async def ping(ctx):
                await ctx.send("Pong!")
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cmd_name = name or func.__name__
            cmd_desc = description or func.__doc__ or cmd_name

            @sosad.slash_command(cmd_name, cmd_desc, **kwargs)
            async def wrapper(ctx: Any) -> None:
                compat_ctx = Context.from_sad(ctx)
                await func(compat_ctx)

            return func

        return decorator

    def event(
        self,
        event_type: type | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register an event handler.

        Usage::

            @bot.event
            async def on_message(message):
                print(message.content)
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if event_type is not None:
                bot_event_type = event_type
            else:
                func_name = func.__name__
                event_name = func_name.replace("on_", "")
                bot_event_type = getattr(
                    hikari, f"{event_name.title().replace('_', '')}Event", None
                )
                if bot_event_type is None:
                    return func

            @sosad.listen(bot_event_type)
            async def wrapper(event: Any) -> None:
                await func(event)

            return func

        return decorator

    def task(
        self,
        interval: float = 60.0,
        *,
        name: str | None = None,
        once: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a background task.

        Usage::

            @bot.task(interval=300)
            async def cleanup():
                await db.purge_old_records()

            @bot.task(interval=10, once=True, name="startup")
            async def on_startup():
                print("Startup check complete")
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            task_name = name or func.__name__
            meta = sosad.tasks.TaskMeta(
                name=task_name,
                handler=func,
                interval=interval,
                once=once,
            )
            if hasattr(self._client, "scheduler"):
                self._client.scheduler.register(meta)
            return func
        return decorator

    def listen(
        self,
        event_type: type | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register an event listener (alias for event)."""
        return self.event(event_type)

    def load_extension(self, name: str) -> None:
        """Load a module (compat for discord.py load_extension).

        Usage::

            bot.load_extension("cogs.music")
        """
        import importlib

        try:
            mod = importlib.import_module(name)
            if hasattr(mod, "setup"):
                mod.setup(self)
        except ImportError:
            pass

    def add_cog(self, cog_instance: Any) -> None:
        """Add a Cog (discord.py compatible).

        Usage::

            class MyCog(discord.Cog):
                ...

            bot.add_cog(MyCog())
        """
        if hasattr(cog_instance, "_set_bot"):
            cog_instance._set_bot(self)
        if hasattr(cog_instance, "cog_load"):
            import asyncio
            from contextlib import suppress
            with suppress(Exception):
                asyncio.ensure_future(cog_instance.cog_load())

        # Register all slash commands on this cog
        for attr_name in dir(cog_instance):
            attr = getattr(cog_instance, attr_name)
            if isinstance(attr, sosad.commands.models.SlashCommandMeta):
                from sosad.commands.registration import get_registry
                # Re-register with bound method
                async def bound_handler(ctx: Any, _attr=attr, _self=cog_instance) -> None:
                    compat_ctx = Context.from_sad(ctx)
                    await _attr.handler(_self, compat_ctx)

                meta = sosad.commands.models.SlashCommandMeta(
                    name=attr.name,
                    description=attr.description,
                    handler=bound_handler,
                    options=attr.options,
                    is_dm_only=attr.is_dm_only,
                    is_guild_only=attr.is_guild_only,
                    nsfw=attr.nsfw,
                    default_member_permissions=attr.default_member_permissions,
                )
                get_registry().add(meta)

    def prefix_command(
        self,
        name: str | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a prefix command (!ping).

        Usage::

            @bot.prefix_command(name="ping")
            async def ping(ctx):
                await ctx.send("Pong!")
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cmd_name = name or func.__name__
            registry = get_prefix_registry()

            async def wrapper(ctx: PrefixContext) -> None:
                await func(ctx)

            registry.add(cmd_name, wrapper)
            return func
        return decorator

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Start the bot.

        Gateway mode: no arguments (uses stored token/intents).
        REST mode: pass host, port, ssl_context, etc.
        """
        self._client.run(*args, **kwargs)

    async def close(self) -> None:
        await self._client.close()


__all__ = ["Bot", "BotMode"]
