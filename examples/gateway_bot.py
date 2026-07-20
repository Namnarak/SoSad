"""Example 1: Basic Gateway bot with slash commands.

Run:
    TOKEN=your_token python examples/gateway_bot.py
"""

from __future__ import annotations

import os

import hikari

import sosad

bot = sosad.Client(
    token=os.environ["TOKEN"],
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)


@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")


@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext) -> None:
    await ctx.respond(f"Hello, {ctx.author.mention}!")


@sosad.slash_command("echo", "Echo your message")
async def echo(
    ctx: sosad.InteractionContext,
    message: str = sosad.annotations.String(description="Message to echo"),
) -> None:
    await ctx.respond(message)


if __name__ == "__main__":
    bot.run()
