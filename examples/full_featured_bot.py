"""Example 5: Full-featured bot — all capabilities.

Run:
    TOKEN=your_token python examples/full_featured_bot.py
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import hikari

import sosad
from sosad.components import Paginator, PersistentView
from sosad.components.storage import FileViewStorage, set_view_storage
from sosad.di import Container
from sosad.middleware import request_metrics

# ── Config ─────────────────────────────────────────────────
class Config(sosad.Settings):
    token: str = os.environ.get("TOKEN", "")
    prefix: str = "!"


config = Config()

# ── DI Setup ──────────────────────────────────────────────
container = Container()


class Database:
    """Fake database for demo purposes."""

    async def query(self, sql: str) -> list[dict]:
        return [{"result": "fake"}]


container.register(Database, instance=Database())

# ── Enable persistent views ───────────────────────────────
set_view_storage(FileViewStorage("views_data"))

# ── Bot Setup ─────────────────────────────────────────────
bot = sosad.Client(
    token=config.token,
    intents=hikari.Intents.ALL_UNPRIVILEGED,
    banner="so sad full-featured",
)

bot.prefix = config.prefix

# ── Middleware ────────────────────────────────────────────
bot.use(request_metrics)
bot.use(sosad.middleware.logging_middleware)


# ── Error Handler ─────────────────────────────────────────
@bot.on_error
async def handle_error(ctx: sosad.InteractionContext, error: Exception) -> None:
    if isinstance(error, sosad.CommandNotFound):
        await ctx.respond("Command not found!")
    elif isinstance(error, sosad.CheckFailed):
        await ctx.respond("You don't have permission!")
    else:
        logger.exception("Unhandled error")
        await ctx.respond(f"Error: {type(error).__name__}: {error}")


# ── Events ────────────────────────────────────────────────
@bot.listen(hikari.StartedEvent)
async def on_ready(event: hikari.StartedEvent) -> None:
    print(f"Logged in as {bot.bot.get_me()}")


# ── Slash Commands ────────────────────────────────────────
@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")


@sosad.slash_command("db", "Query database (uses DI)")
async def db_query(
    ctx: sosad.InteractionContext,
    db: Database = sosad.inject(Database),
) -> None:
    results = await db.query("SELECT 1")
    await ctx.respond(f"DB result: {results}")


# ── Prefix Commands ───────────────────────────────────────
@bot.prefix_command(name="echo")
async def echo(ctx: sosad.PrefixContext, *, text: str) -> None:
    await ctx.send(text)


@sosad.check("owner_only")
@bot.prefix_command(name="eval")
async def eval_cmd(ctx: sosad.PrefixContext, *, code: str) -> None:
    """Owner-only eval command."""
    try:
        result = eval(code)
        await ctx.send(f"```\n{result}\n```")
    except Exception as e:
        await ctx.send(f"```\nError: {e}\n```")


@sosad.slash_command("cooldown", "Test rate limiting")
@sosad.cooldown(1, 10, sosad.BucketScope.USER)  # 1 use per 10s per user
async def cooldown_cmd(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("This has a cooldown!")


from sosad import guild_only


@sosad.slash_command("admin", "Admin only")
@guild_only
@sosad.is_owner
async def admin_only(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Welcome, owner!")


# ── Persistent View ───────────────────────────────────────
@PersistentView.register("ticket_view", timeout=3600)
class TicketView(PersistentView):
    def __init__(self, ticket_id: str) -> None:
        super().__init__()
        self.ticket_id = ticket_id
        self.add_button("close", "Close Ticket", sosad.ButtonBuilder.DANGER)

    async def on_button(self, ctx: sosad.ComponentContext, button_id: str) -> None:
        if button_id == "close":
            await ctx.respond(f"Ticket {self.ticket_id} closed!")


@sosad.slash_command("ticket", "Create a ticket")
async def create_ticket(ctx: sosad.InteractionContext) -> None:
    from uuid import uuid4
    view = TicketView(ticket_id=str(uuid4()))
    view.bind(ctx)
    await ctx.respond("Ticket created!").set_components(view).send()


# ── Paginator ─────────────────────────────────────────────
@Paginator.register("server_info")
class ServerInfoPaginator(Paginator):
    def __init__(self, guild_name: str) -> None:
        super().__init__(pages=[
            {"title": f"{guild_name} — Info", "desc": "Server info page"},
            {"title": f"{guild_name} — Stats", "desc": "Member count, channels..."},
            {"title": f"{guild_name} — Roles", "desc": "Role list"},
        ])

    async def render_page(self, page: dict) -> sosad.ResponseBuilder:
        embed = hikari.Embed(
            title=page["title"],
            description=page["desc"],
            colour=0x9B59B6,
        )
        return sosad.ResponseBuilder().embed(embed)


@sosad.slash_command("server", "Show server info")
async def server_info(ctx: sosad.InteractionContext) -> None:
    guild = bot.bot.cache.get_guild(ctx.guild_id)
    paginator = ServerInfoPaginator(guild.name if guild else "Unknown")
    paginator.bind(ctx)
    await paginator.send(ctx)


# ── Background Tasks ──────────────────────────────────────
@bot.task(minutes=5)
async def clean_cache() -> None:
    """Clean old views every 5 minutes."""
    from sosad.components.storage import get_view_storage
    expired = await get_view_storage().cleanup_expired(3600)
    if expired:
        print(f"Cleaned {expired} expired views")


if __name__ == "__main__":
    with sosad.configure_logging():
        bot.run()
