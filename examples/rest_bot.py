"""Example 2: REST mode bot (no gateway).

Run:
    TOKEN=your_token PUBLIC_KEY=your_key python examples/rest_bot.py
"""

from __future__ import annotations

import os

import hikari

import sosad

bot = sosad.RESTClient(
    token=os.environ["TOKEN"],
    public_key=os.environ["PUBLIC_KEY"],
)

@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong! (REST mode)").send()


@sosad.slash_command("stats", "Bot statistics")
async def stats(ctx: sosad.InteractionContext) -> None:
    embed = hikari.Embed(
        title="Bot Stats",
        description="Running in REST mode",
        colour=0x00FF00,
    )
    await ctx.respond().embed(embed).send()


bot.run(host="0.0.0.0", port=8080, path="/interactions")
