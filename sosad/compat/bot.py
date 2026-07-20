"""discord.py-compatible Bot class wrapping SoSad Client."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import hikari

from sosad.compat.context import Context
from sosad.core.client import Client


class Bot(Client):
    """discord.py-compatible Bot that wraps SoSad Client.

    Usage::

        import sosad.compat as discord

        bot = discord.Bot(intents=discord.Intents.default())

        @bot.command(name="ping")
        async def ping(ctx):
            await ctx.send("Pong!")

        bot.run("TOKEN")
    """

    def __init__(
        self,
        *,
        command_prefix: str = "!",
        intents: hikari.Intents | None = None,
        token: str | None = None,
        **kwargs: Any,
    ) -> None:
        if intents is None:
            intents = hikari.Intents.ALL_UNPRIVILEGED

        super().__init__(
            token=token or "",
            intents=intents,
            **kwargs,
        )
        self._command_prefix = command_prefix
        self._prefix_commands: dict[str, Callable[..., Any]] = {}

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

    def event(self, event_type: type | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register an event handler.

        Usage::

            @bot.event
            async def on_message(message):
                print(message.content)
        """
        import sosad

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if event_type is not None:
                bot_event_type = event_type
            else:
                # Derive from function name: on_message -> MessageCreateEvent
                func_name = func.__name__
                event_name = func_name.replace("on_", "")
                bot_event_type = getattr(hikari, f"{event_name.title().replace('_', '')}Event", None)
                if bot_event_type is None:
                    return func

            @sosad.listen(bot_event_type)
            async def wrapper(event: Any) -> None:
                await func(event)

            return func
        return decorator

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


# Import sosad at module level for decorator use
import sosad  # noqa: E402

__all__ = ["Bot"]
