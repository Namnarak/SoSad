"""Example: Basic SoSad bot."""

import hikari
import sosad

# Decorators register commands at import time
@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond().content("Pong!").send()


@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext) -> None:
    await ctx.respond().content(f"Hello, {ctx.author.mention}!").send()


if __name__ == "__main__":
    bot = sosad.Client(
        token="YOUR_TOKEN_HERE",
        intents=hikari.Intents.ALL_UNPRIVILEGED,
    )
    bot.run()
