"""discord.py compatibility layer.

Usage::

    # Just change the import:
    # import discord
    import sosad.compat as discord

    bot = discord.Bot(intents=discord.Intents.default())

    @bot.command(name="ping")
    async def ping(ctx):
        embed = discord.Embed(title="Pong!", colour=discord.Colour.green())
        await ctx.send(embed=embed)

    bot.run("TOKEN")

SoSad handles the rest — rate limits, error handling, type safety, etc.
"""

# Direct re-exports from hikari
from hikari import Intents as Intents
from hikari import PermissionOverwrite as PermissionOverwrite
from hikari import Permissions as Permissions

from sosad.compat.bot import Bot
from sosad.compat.colour import Color, Colour
from sosad.compat.context import Context
from sosad.compat.embed import Embed
from sosad.compat.ext import Cog, cog
from sosad.compat.file import File
from sosad.compat.utils import (
    escape_markdown,
    escape_markdown_and_mentions,
    escape_mentions,
    find,
    format_dt,
    get,
    snowflake_time,
    utcnow,
)

__all__ = [
    "Bot",
    "Context",
    "Cog",
    "cog",
    "Embed",
    "Colour",
    "Color",
    "File",
    "Intents",
    "Permissions",
    "PermissionOverwrite",
    "get",
    "find",
    "escape_markdown",
    "escape_mentions",
    "escape_markdown_and_mentions",
    "utcnow",
    "format_dt",
    "snowflake_time",
]
