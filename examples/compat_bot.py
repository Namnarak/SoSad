"""Example 3: discord.py compat mode.

Shows how to use discord.py-compatible API.

Run:
    TOKEN=your_token python examples/compat_bot.py
"""

from __future__ import annotations

import os

import hikari

import sosad.compat as discord

bot = discord.Bot(
    command_prefix="!",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
    token=os.environ["TOKEN"],
)


# Prefix command
@bot.prefix_command(name="ping")
async def ping(ctx: discord.Context) -> None:
    await ctx.send("Pong!")


# Slash command (discord.py compat)
@bot.command(name="hello")
async def hello(ctx: discord.Context) -> None:
    embed = discord.Embed(
        title="Hello!",
        description=f"Hello, {ctx.author.mention}!",
        colour=discord.Colour.green(),
    )
    embed.add_field(name="User ID", value=str(ctx.author.id), inline=True)
    embed.add_field(name="Channel", value=str(ctx.channel_id), inline=True)
    await ctx.send(embed=embed)


# App commands style
@discord.app_commands.command(name="echo", description="Echo your message")
async def echo(ctx: discord.Context, message: str) -> None:
    await ctx.send(f"You said: {message}")


# Using utils
@bot.prefix_command(name="finduser")
async def finduser(ctx: discord.Context, *, name: str) -> None:
    members = await ctx.bot.rest.fetch_members(ctx.guild_id)
    user = discord.utils.get(members, name=name)
    if user:
        await ctx.send(f"Found: {user.mention}")
    else:
        await ctx.send("User not found")


if __name__ == "__main__":
    bot.run()
