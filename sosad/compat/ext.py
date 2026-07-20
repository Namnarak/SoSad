"""discord.py-compatible Cog system."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Cog:
    """discord.py-compatible Cog class.

    Usage::

        class MyCog(discord.Cog):
            @discord.command(name="ping")
            async def ping(self, ctx):
                await ctx.send("Pong!")

        bot.add_cog(MyCog())
    """

    def __init__(self) -> None:
        self.bot: Any = None

    def _set_bot(self, bot: Any) -> None:
        self.bot = bot


def cog(cls: type) -> type:
    """Decorator to mark a class as a Cog.

    Usage::

        @discord.cog
        class MyCog:
            @discord.command(name="ping")
            async def ping(self, ctx):
                await ctx.send("Pong!")
    """
    if not issubclass(cls, Cog):
        bases = (Cog, *cls.__bases__)
        cls = type(cls.__name__, bases, dict(cls.__dict__))
    return cls


__all__ = ["Cog", "cog"]
