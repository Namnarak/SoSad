"""A discord.py-shaped facade over SoSad's Gateway and REST clients."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import sys
from collections.abc import Callable
from typing import Any, Literal

import hikari

import sosad
from sosad.commands.prefix import PrefixContext, get_prefix_registry
from sosad.compat._awaitable import DeferredAwaitable, ImmediateAwaitable
from sosad.compat.app_commands import CommandTree
from sosad.compat.context import Context
from sosad.core.base_client import BaseClient
from sosad.core.client import Client
from sosad.core.rest_client import RESTClient

BotMode = Literal["gateway", "rest"]


class Bot:
    """Compatibility Bot supporting the constructor/run split from discord.py.

    ``token`` is optional at construction time and may be supplied to
    :meth:`run`, matching discord.py's normal usage.  A real token is only
    required when the gateway or REST server is actually started.
    """

    def __init__(
        self,
        command_prefix: Any = "!",
        *,
        mode: BotMode = "gateway",
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
        self._token = token
        self.help_command = kwargs.pop("help_command", None)
        tree_cls = kwargs.pop("tree_cls", CommandTree)
        self.case_insensitive = kwargs.pop("case_insensitive", False)
        self.strip_after_prefix = kwargs.pop("strip_after_prefix", False)
        # These are valid discord.py constructor options, but are not Hikari
        # GatewayBot options.  Keep them as attributes instead of forwarding
        # them into Hikari and causing an unexpected-keyword error at run().
        for option in (
            "activity",
            "status",
            "allowed_mentions",
            "chunk_guilds_at_startup",
            "member_cache_flags",
            "max_messages",
            "owner_id",
            "owner_ids",
        ):
            setattr(self, option, kwargs.pop(option, None))

        if intents is None:
            intents = hikari.Intents.ALL_UNPRIVILEGED
        self.intents = intents
        native_intents = (
            intents.to_hikari() if hasattr(intents, "to_hikari") else intents
        )

        client_token = token or ""
        if mode == "rest":
            self._client: BaseClient = RESTClient(
                token=client_token,
                public_key=public_key,
                logs=logs,
                banner=banner,
                auto_discover_plugins=auto_discover_plugins,
                **kwargs,
            )
        else:
            self._client = Client(
                token=client_token,
                intents=native_intents,
                logs=logs,
                banner=banner,
                auto_discover_plugins=auto_discover_plugins,
                **kwargs,
            )

        self._prefix_commands: dict[str, Callable[..., Any]] = {}
        self._cogs: dict[str, Any] = {}
        self._extensions: dict[str, Any] = {}
        self._tree = tree_cls(self)
        self._ready = asyncio.Event()
        self._setup_hook_registered = False
        self._events_registered = False
        self._closed = False
        self._presence: Any = None
        if hasattr(self._client, "prefix") and isinstance(command_prefix, str):
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
        return getattr(self._client, "scheduler", None)

    @property
    def bot(self) -> Any:
        try:
            return self._client.bot
        except RuntimeError:
            return None

    @property
    def rest(self) -> Any:
        try:
            return self._client.rest
        except (AttributeError, RuntimeError):
            return None

    @property
    def http(self) -> Any:
        """discord.py's HTTP attribute, mapped to Hikari's REST client."""
        return self.rest

    @property
    def tree(self) -> CommandTree:
        return self._tree

    @property
    def cogs(self) -> dict[str, Any]:
        return dict(self._cogs)

    @property
    def guilds(self) -> list[Any]:
        client = self.bot
        if client is None or not hasattr(client, "cache"):
            return []
        return list(client.cache.get_available_guilds_view().values())

    @property
    def user(self) -> Any:
        client = self.bot
        return client.get_me() if client is not None else None

    @property
    def latency(self) -> float:
        client = self.bot
        return float(getattr(client, "heartbeat_latency", 0.0) or 0.0)

    @property
    def is_closed(self) -> bool:
        return self._closed

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

    # ── discord.py-compatible decorators ──

    def command(
        self,
        name: str | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a top-level slash command and return the original callback."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._register_callback(func, name=name, description=description, **kwargs)
            return func

        return decorator

    def event(
        self,
        event_type: type | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            resolved_type = event_type or self._event_type_for_name(func.__name__)
            if resolved_type is not None and hasattr(self._client, "listen"):
                self._client.listen(resolved_type)(self._adapt_event(func, resolved_type))
            return func

        return decorator

    def task(
        self,
        interval: float = 60.0,
        *,
        name: str | None = None,
        once: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            task_name = name or func.__name__
            meta = sosad.tasks.TaskMeta(
                name=task_name,
                handler=func,
                interval=interval,
                once=once,
            )
            self._client.scheduler.register(meta)
            return func

        return decorator

    def listen(
        self,
        event_type: type | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.event(event_type)

    # ── Extensions and cogs ──

    def load_extension(self, name: str) -> DeferredAwaitable:
        return DeferredAwaitable(lambda: self._load_extension(name))

    async def _load_extension(self, name: str) -> Any:
        if name in self._extensions:
            from sosad.compat.ext.commands import ExtensionAlreadyLoaded

            raise ExtensionAlreadyLoaded(name)
        module = importlib.import_module(name)
        setup = getattr(module, "setup", None)
        if setup is not None:
            result = setup(self)
            if inspect.isawaitable(result):
                await result
        self._extensions[name] = module
        return module

    def unload_extension(self, name: str) -> DeferredAwaitable:
        return DeferredAwaitable(lambda: self._unload_extension(name))

    async def _unload_extension(self, name: str) -> Any:
        if name not in self._extensions:
            from sosad.compat.ext.commands import ExtensionNotLoaded

            raise ExtensionNotLoaded(name)
        module = self._extensions.pop(name)
        prefix = f"{name}."
        for module_name in list(sys.modules):
            if module_name == name or module_name.startswith(prefix):
                sys.modules.pop(module_name, None)
        return module

    def reload_extension(self, name: str) -> DeferredAwaitable:
        async def reload() -> Any:
            if name in self._extensions:
                await self._unload_extension(name)
            return await self._load_extension(name)

        return DeferredAwaitable(lambda: reload())

    def add_cog(self, cog_instance: Any, *, override: bool = False) -> ImmediateAwaitable:
        name = getattr(type(cog_instance), "__cog_name__", type(cog_instance).__name__.lower())
        if name in self._cogs and not override:
            raise ValueError(f"Cog {name!r} is already registered")
        self._cogs[name] = cog_instance
        if hasattr(cog_instance, "_set_bot"):
            cog_instance._set_bot(self)
        for command in self._commands_from_cog(cog_instance):
            self._register_cog_command(cog_instance, command)
        return ImmediateAwaitable(cog_instance)

    def remove_cog(self, name: str) -> ImmediateAwaitable:
        return ImmediateAwaitable(self._cogs.pop(name, None))

    def get_cog(self, name: str) -> Any | None:
        return self._cogs.get(name)

    def get_command(self, name: str) -> Any | None:
        for cog in self._cogs.values():
            for command in self._commands_from_cog(cog):
                if command.name == name or name in command.aliases:
                    return command
        return None

    # ── Prefix helpers and runtime helpers ──

    def prefix_command(
        self,
        name: str | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        del kwargs

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cmd_name = name or func.__name__
            registry = get_prefix_registry()

            async def wrapper(ctx: PrefixContext) -> None:
                result = func(Context.from_prefix(ctx, bot=self))
                if inspect.isawaitable(result):
                    await result

            registry.add(cmd_name, wrapper)
            self._prefix_commands[cmd_name] = func
            return func

        return decorator

    async def process_commands(self, message: Any) -> None:
        del message

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    async def change_presence(self, *, activity: Any = None, **kwargs: Any) -> None:
        self._presence = activity
        client = self.bot
        if client is None or not hasattr(client, "update_presence"):
            return
        if hasattr(activity, "to_hikari"):
            activity = activity.to_hikari()
        await client.update_presence(activity=activity, **kwargs)

    async def is_owner(self, user: Any) -> bool:
        del user
        owner_ids = getattr(self, "owner_ids", None)
        owner_id = getattr(self, "owner_id", None)
        return bool(owner_ids or owner_id)

    def get_user(self, user_id: int) -> Any | None:
        client = self.bot
        if client is not None and hasattr(client, "cache"):
            return client.cache.get_user(hikari.Snowflake(user_id))
        return None

    async def fetch_user(self, user_id: int) -> Any:
        if self.rest is None:
            raise RuntimeError("Bot has not been started")
        return await self.rest.fetch_user(user_id)

    async def application_info(self) -> Any:
        if self.rest is None:
            raise RuntimeError("Bot has not been started")
        return await self.rest.fetch_my_application()

    # ── Start/stop ──

    def run(self, token: str | None = None, *args: Any, **kwargs: Any) -> None:
        # discord.py accepts this logging switch; Hikari configures logging
        # before startup, so it has no equivalent runtime argument.
        kwargs.pop("root_logger", None)
        if token is not None:
            self._token = token
            self._client._token = token
        if not self._token:
            raise ValueError("token is required when the bot is started")
        if self._mode == "gateway":
            self._install_subclass_runtime()
        self._client.run(*args, **kwargs)

    async def close(self) -> None:
        self._closed = True
        self._ready.set()
        await self._client.close()

    # ── Internal translation ──

    def _register_callback(self, callback: Callable[..., Any], **kwargs: Any) -> None:
        from sosad.compat.ext.commands import Command

        command = Command(callback, kind="slash", **kwargs)
        self._register_command(self, command, callback)

    def _register_app_command(self, command: Any, *, guild: Any = None) -> None:
        if guild is not None:
            return
        if not hasattr(command, "callback"):
            return
        if getattr(command, "type", None) == "context_menu":
            from sosad.commands.models import SlashCommandMeta
            from sosad.commands.registration import get_registry

            annotation = getattr(command.callback, "__annotations__", {})
            command_type = (
                hikari.CommandType.USER
                if "user" in annotation
                else hikari.CommandType.MESSAGE
            )

            async def handler(ctx: Any) -> Any:
                from sosad.compat.interaction import wrap_interaction

                result = command.callback(wrap_interaction(ctx.interaction))
                if inspect.isawaitable(result):
                    return await result
                return result

            get_registry().add(
                SlashCommandMeta(
                    name=command.name,
                    description=command.description,
                    handler=handler,
                    command_type=command_type,
                )
            )
            return
        self._register_command(
            self,
            command,
            command.callback,
            interaction_style=bool(getattr(command, "is_app_command", False)),
        )

    def _register_cog_command(self, cog: Any, command: Any) -> None:
        from sosad.compat.ext.commands import Group

        if isinstance(command, Group) and command.kind in ("hybrid", "slash"):
            self.tree._global.setdefault(command.name, command)
            self._register_group(command)
            for child in command.children.values():
                self._register_subcommand(cog, command, child)
            return
        if command.kind in ("hybrid", "slash"):
            self.tree._global.setdefault(command.name, command)
            self._register_command(
                cog,
                command,
                command.callback,
                interaction_style=bool(getattr(command, "is_app_command", False)),
            )
        else:
            self._register_prefix_cog_command(cog, command)
        for child in getattr(command, "children", {}).values():
            if command.kind in ("hybrid", "slash"):
                self._register_subcommand(cog, command, child)

    def _register_group(self, command: Any) -> None:
        from sosad.commands.models import CommandGroupMeta
        from sosad.commands.registration import get_registry

        get_registry().add(
            CommandGroupMeta(
                name=command.name,
                description=command.description,
            )
        )

    def _register_command(
        self,
        owner: Any,
        command: Any,
        callback: Any,
        *,
        interaction_style: bool = False,
    ) -> None:
        from dataclasses import replace

        from sosad.commands.decorators import _extract_options
        from sosad.commands.models import SlashCommandMeta
        from sosad.commands.registration import get_registry

        descriptions = getattr(callback, "_sosad_descriptions", {})
        options = list(_extract_options(callback, descriptions))
        choices = getattr(callback, "_sosad_choices", {})
        for index, option in enumerate(options):
            values = choices.get(option.name)
            if values:
                options[index] = replace(
                    option,
                    choices=tuple((value["name"], value["value"]) for value in values),
                )

        async def handler(ctx: Any, **values: Any) -> Any:
            if interaction_style:
                from sosad.compat.interaction import wrap_interaction

                result = callback(
                    owner,
                    wrap_interaction(ctx.interaction),
                    **values,
                ) if owner is not self else callback(
                    wrap_interaction(ctx.interaction),
                    **values,
                )
            else:
                compat_ctx = Context.from_sad(ctx, bot=self)
                if owner is self:
                    result = callback(compat_ctx, **values)
                else:
                    result = callback(owner, compat_ctx, **values)
            if inspect.isawaitable(result):
                return await result
            return result

        meta = SlashCommandMeta(
            name=command.name,
            description=command.description,
            handler=handler,
            options=tuple(options),
            is_guild_only=bool(getattr(callback, "_sosad_guild_only", False)),
        )
        get_registry().add(meta)

    def _register_subcommand(self, cog: Any, group: Any, command: Any) -> None:
        from dataclasses import replace

        from sosad.commands.decorators import _extract_options
        from sosad.commands.models import SubCommandMeta
        from sosad.commands.registration import get_registry

        callback = command.callback
        descriptions = getattr(callback, "_sosad_descriptions", {})
        options = list(_extract_options(callback, descriptions))
        choices = getattr(callback, "_sosad_choices", {})
        for index, option in enumerate(options):
            values = choices.get(option.name)
            if values:
                options[index] = replace(
                    option,
                    choices=tuple((value["name"], value["value"]) for value in values),
                )

        async def handler(ctx: Any, **values: Any) -> Any:
            compat_ctx = Context.from_sad(ctx, bot=self)
            result = callback(cog, compat_ctx, **values)
            if inspect.isawaitable(result):
                return await result
            return result

        get_registry().add(
            SubCommandMeta(
                group=group.name,
                name=command.name,
                description=command.description,
                handler=handler,
                options=tuple(options),
            )
        )

    def _register_prefix_cog_command(self, cog: Any, command: Any) -> None:
        registry = get_prefix_registry()

        async def handler(ctx: PrefixContext) -> None:
            compat_ctx = Context.from_prefix(ctx, bot=self)
            result = command.callback(cog, compat_ctx)
            if inspect.isawaitable(result):
                await result

        registry.add(command.name, handler)

    @staticmethod
    def _commands_from_cog(cog: Any) -> list[Any]:
        from sosad.compat.ext.commands import Command

        return [value for value in vars(type(cog)).values() if isinstance(value, Command)]

    @staticmethod
    def _event_type_for_name(name: str) -> type[hikari.Event] | None:
        mapping: dict[str, type[hikari.Event]] = {
            "on_ready": hikari.StartedEvent,
            "on_message": hikari.GuildMessageCreateEvent,
            "on_interaction": hikari.InteractionCreateEvent,
        }
        return mapping.get(name)

    @staticmethod
    def _adapt_event(callback: Callable[..., Any], event_type: type) -> Callable[..., Any]:
        async def handler(event: Any) -> Any:
            value = event.message if event_type is hikari.GuildMessageCreateEvent else event
            result = callback(value)
            if inspect.isawaitable(result):
                return await result
            return result

        return handler

    def _install_subclass_runtime(self) -> None:
        if self._events_registered:
            return
        self._events_registered = True
        setup_hook = getattr(type(self), "setup_hook", None)
        if setup_hook is not None:
            async def setup(event: Any) -> None:
                del event
                await setup_hook(self)
                self._ready.set()

            self._client.listen(hikari.StartedEvent)(setup)

        for name in ("on_message", "on_interaction", "on_ready"):
            callback = getattr(type(self), name, None)
            if callback is None:
                continue
            event_type = self._event_type_for_name(name)
            if event_type is not None:
                bound = callback.__get__(self)
                self._client.listen(event_type)(self._adapt_event(bound, event_type))

    async def _sync_tree(self, *, guild: Any = None) -> None:
        del guild
        if self.bot is not None and hasattr(self._client, "_sync_all_commands"):
            await self._client._sync_all_commands()


__all__ = ["Bot", "BotMode"]
