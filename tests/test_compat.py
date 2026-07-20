"""Tests for discord.py compatibility layer."""

import hikari
from sosad.compat.bot import Bot
from sosad.compat.context import Context
from sosad.compat.ext import Cog, cog


def test_bot_init():
    bot = Bot(token="test", intents=hikari.Intents.ALL_UNPRIVILEGED)
    assert bot._command_prefix == "!"


def test_bot_custom_prefix():
    bot = Bot(token="test", intents=hikari.Intents.ALL_UNPRIVILEGED, command_prefix="?")
    assert bot._command_prefix == "?"


def test_bot_command_decorator():
    bot = Bot(token="test", intents=hikari.Intents.ALL_UNPRIVILEGED)

    @bot.command(name="ping")
    async def ping(ctx):
        await ctx.send("Pong!")

    assert ping is not None


def test_bot_event_decorator():
    bot = Bot(token="test", intents=hikari.Intents.ALL_UNPRIVILEGED)

    @bot.event
    async def on_ready():
        pass

    assert on_ready is not None


def test_context_send():
    from unittest.mock import MagicMock, AsyncMock

    mock_ctx = MagicMock()
    mock_ctx.respond.return_value = MagicMock()
    mock_ctx.respond.return_value.content = MagicMock(return_value=mock_ctx.respond.return_value)
    mock_ctx.respond.return_value.ephemeral = MagicMock(return_value=mock_ctx.respond.return_value)
    mock_ctx.respond.return_value.send = AsyncMock()

    compat_ctx = Context(mock_ctx)
    assert compat_ctx.interaction == mock_ctx.interaction


def test_cog_class():
    class MyCog(Cog):
        pass

    instance = MyCog()
    assert isinstance(instance, Cog)


def test_cog_decorator():
    @cog
    class MyCog:
        pass

    assert issubclass(MyCog, Cog)
    instance = MyCog()
    assert isinstance(instance, Cog)
