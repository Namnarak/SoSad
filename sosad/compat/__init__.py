"""discord.py compatibility layer.

Usage::

    # Just change the import:
    # import discord
    import sosad.compat as discord

    bot = discord.Bot(intents=discord.Intents.default())

    @bot.command(name="ping")
    async def ping(ctx):
        await ctx.send("Pong!")

    bot.run("TOKEN")

SoSad handles the rest — rate limits, error handling, type safety, etc.
"""
from sosad.compat.bot import Bot
from sosad.compat.context import Context
from sosad.compat.ext import Cog, cog

__all__ = ["Bot", "Context", "Cog", "cog"]
