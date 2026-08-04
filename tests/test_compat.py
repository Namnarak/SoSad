"""Tests for discord.py compatibility layer."""

import hikari
import pytest

from sosad.compat import Intents
from sosad.compat.bot import Bot
from sosad.compat.context import Context
from sosad.compat.ext import Cog, cog


def test_drop_in_import_paths():
    import discord
    from discord import app_commands, ui
    from discord.ext import commands, tasks

    assert discord.Intents.default() == hikari.Intents.ALL_UNPRIVILEGED
    assert commands.Bot is Bot
    assert app_commands.CommandTree is not None
    assert ui.View is not None
    assert tasks.loop is not None


def test_bot_init():
    bot = Bot(token="test", intents=hikari.Intents.ALL_UNPRIVILEGED)
    assert bot._command_prefix == "!"


def test_bot_can_receive_token_at_run_time():
    bot = Bot(intents=hikari.Intents.ALL_UNPRIVILEGED)
    assert bot._token is None
    with pytest.raises(ValueError, match="token is required"):
        bot.run()


@pytest.mark.asyncio
async def test_cog_and_ui_compatibility():
    from discord import ButtonStyle, SelectOption, TextStyle, ui
    from discord.ext import commands

    class Demo(commands.Cog, name="demo"):
        def __init__(self, bot):
            self.bot = bot

        @commands.hybrid_command(name="hello", description="Say hello")
        async def hello(self, context: commands.Context) -> None:
            await context.send("hello")

    class DemoView(ui.View):
        @ui.button(label="Go", style=ButtonStyle.blurple)
        async def go(self, interaction, button):
            del interaction, button

    class DemoModal(ui.Modal, title="Feedback"):
        answer = ui.TextInput(label="Answer", style=TextStyle.long)

    bot = commands.Bot(intents=hikari.Intents.ALL_UNPRIVILEGED)
    await bot.add_cog(Demo(bot))
    view = DemoView()
    modal = DemoModal()
    select = ui.Select(options=[SelectOption(label="One")])

    assert bot.get_cog("demo").get_commands()[0].name == "hello"
    assert view.children[0].label == "Go"
    assert view.build_rows()[0][0]["style"] == hikari.ButtonStyle.PRIMARY.value
    assert modal.title == "Feedback"
    assert (
        modal.build()["components"][0]["components"][0]["style"]
        == hikari.TextInputStyle.PARAGRAPH.value
    )
    assert select.to_dict()["options"][0]["value"] == "One"


def test_compat_intents_constructors():
    assert Intents.default() == hikari.Intents.ALL_UNPRIVILEGED
    assert Intents.all() == hikari.Intents.ALL
    assert Intents.none() == hikari.Intents.NONE
    assert Intents.GUILDS == hikari.Intents.GUILDS
    assert Intents(0) == hikari.Intents.NONE


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
    from unittest.mock import AsyncMock, MagicMock

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
