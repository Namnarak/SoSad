"""Extended tests for the discord.py compatibility layer."""

from __future__ import annotations

from datetime import datetime, timezone

import hikari
import pytest

from sosad.compat import Object as SoSadObject
from sosad.compat.colour import Color, Colour
from sosad.compat.embed import Embed
from sosad.compat.utils import (
    escape_markdown,
    escape_mentions,
    find,
    format_dt,
    get,
    snowflake_time,
    utcnow,
)
from sosad.compat.voice import VoiceChannel, VoiceClient


class TestEmbed:
    def test_basic_embed(self):
        embed = Embed(title="Hello", description="World")
        assert embed.title == "Hello"
        assert embed.description == "World"

    def test_add_field(self):
        embed = Embed()
        embed.add_field(name="Field 1", value="Value 1")
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "Field 1"
        assert embed.fields[0].inline is True

    def test_add_field_not_inline(self):
        embed = Embed()
        embed.add_field(name="F", value="V", inline=False)
        assert embed.fields[0].inline is False

    def test_remove_field(self):
        embed = Embed()
        embed.add_field(name="A", value="1")
        embed.add_field(name="B", value="2")
        embed.remove_field(0)
        assert len(embed.fields) == 1
        assert embed.fields[0].name == "B"

    def test_clear_fields(self):
        embed = Embed()
        embed.add_field(name="A", value="1")
        embed.add_field(name="B", value="2")
        embed.clear_fields()
        assert len(embed.fields) == 0

    def test_set_field_at(self):
        embed = Embed()
        embed.add_field(name="A", value="1")
        embed.add_field(name="B", value="2")
        embed.set_field_at(0, name="X", value="99")
        assert embed.fields[0].name == "X"
        assert embed.fields[0].value == "99"

    def test_set_field_at_out_of_range(self):
        embed = Embed()
        embed.add_field(name="A", value="1")
        with pytest.raises(IndexError):
            embed.set_field_at(5, name="X", value="99")

    def test_set_footer(self):
        embed = Embed()
        embed.set_footer(text="Footer text")
        assert embed.footer.text == "Footer text"

    def test_set_footer_with_icon(self):
        embed = Embed()
        embed.set_footer(text="Footer", icon_url="https://example.com/icon.png")
        assert embed.footer.text == "Footer"

    def test_set_image(self):
        embed = Embed()
        embed.set_image(url="https://example.com/image.png")
        assert embed.image is not None

    def test_set_thumbnail(self):
        embed = Embed()
        embed.set_thumbnail(url="https://example.com/thumb.png")
        assert embed.thumbnail is not None

    def test_set_author(self):
        embed = Embed()
        embed.set_author(name="Author Name")
        assert embed.author.name == "Author Name"

    def test_set_author_with_icon(self):
        embed = Embed()
        embed.set_author(name="Author", icon_url="https://example.com/auth.png")
        assert embed.author.name == "Author"

    def test_colour_kwarg(self):
        embed = Embed(title="Test", colour=0xFF0000)
        assert embed.colour is not None
        assert int(embed.colour) == 0xFF0000

    def test_color_alias(self):
        embed = Embed(title="Test", color=0x00FF00)
        assert embed.colour is not None
        assert int(embed.colour) == 0x00FF00

    def test_to_dict(self):
        embed = Embed(title="T", description="D", colour=0xFF0000)
        embed.add_field(name="F1", value="V1")
        embed.set_footer(text="Footer")
        embed.set_author(name="Author")
        embed.set_image(url="https://example.com/img.png")
        embed.set_thumbnail(url="https://example.com/thumb.png")

        d = embed.to_dict()
        assert d["title"] == "T"
        assert d["description"] == "D"
        assert d["color"] is not None
        assert len(d["fields"]) == 1

    def test_empty_embed(self):
        embed = Embed()
        assert embed.title is None
        assert embed.description is None


class TestColour:
    def test_from_int(self):
        c = Colour(0xFF0000)
        assert int(c) == 0xFF0000
        assert isinstance(c, Colour)

    def test_named_colours(self):
        for name in ["green", "red", "blue", "yellow", "orange", "purple",
                      "magenta", "white", "gold", "teal", "pink",
                      "dark_green", "dark_red", "dark_blue", "dark_gold",
                      "dark_teal", "blurple", "greyple", "dark_theme",
                      "brand_green", "brand_red", "light_grey", "darker_grey",
                      "darker_gray", "fb_white", "fuse"]:
            color = getattr(Colour, name)()
            assert isinstance(color, Colour), f"{name}() returned {type(color)}"

    def test_color_alias(self):
        assert Color is Colour

    def test_from_hikari_colour(self):
        hc = hikari.Colour(0x123456)
        c = Colour(hc)
        assert int(c) == 0x123456

    def test_equality(self):
        assert Colour(0xFF0000) == Colour(0xFF0000)
        assert Colour(0xFF0000) != Colour(0x00FF00)


class TestObject:
    def test_basic_object(self):
        obj = SoSadObject(id=12345)
        assert obj.id == 12345
        assert int(obj) == 12345

    def test_equality(self):
        a = SoSadObject(id=1)
        b = SoSadObject(id=1)
        c = SoSadObject(id=2)
        assert a == b
        assert a != c

    def test_hashing(self):
        s = {SoSadObject(id=1), SoSadObject(id=1), SoSadObject(id=2)}
        assert len(s) == 2

    def test_repr(self):
        obj = SoSadObject(id=42)
        assert "42" in repr(obj)


class TestUtils:
    def test_get(self):
        class User:
            def __init__(self, name):
                self.name = name
        items = [User("Alice"), User("Bob")]
        result = get(items, name="Alice")
        assert result is not None
        assert result.name == "Alice"

    def test_get_no_match(self):
        class User:
            def __init__(self, name):
                self.name = name
        items = [User("Alice")]
        result = get(items, name="Charlie")
        assert result is None

    def test_find(self):
        items = [1, 2, 3, 4, 5]
        result = find(lambda x: x > 3, items)
        assert result == 4

    def test_find_no_match(self):
        result = find(lambda x: x > 10, [1, 2, 3])
        assert result is None

    def test_escape_markdown(self):
        result = escape_markdown("Hello **world** *italic*")
        assert "**" not in result
        assert "\\*\\*" in result or "\\*" in result

    def test_escape_mentions(self):
        result = escape_mentions("@everyone check @here and @user")
        assert "everyone" in result  # Mention is broken, but word is preserved
        assert "@" in result  # @ is still there, but mention won't ping

    def test_utcnow(self):
        now = utcnow()
        assert isinstance(now, datetime)
        assert now.tzinfo is timezone.utc

    def test_snowflake_time(self):
        # Snowflake for a known time
        dt = snowflake_time(175928847299117063)
        assert isinstance(dt, datetime)

    def test_format_dt(self):
        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = format_dt(dt)
        assert result.startswith("<t:")
        assert result.endswith(">")

    def test_format_dt_with_style(self):
        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = format_dt(dt, style="R")
        assert "<t:" in result
        assert ":R>" in result


class TestWebhook:
    def test_webhook_from_url(self):
        from sosad.compat.webhook import Webhook
        wb = Webhook.from_url("https://discord.com/api/webhooks/123/abc")
        assert wb.id == 123
        assert wb.token == "abc"

    def test_webhook_url_parse(self):
        from sosad.compat.webhook import Webhook
        wb = Webhook.from_url("https://discord.com/api/webhooks/456/def")
        assert wb.id == 456
        assert wb.token == "def"


class TestVoice:
    def test_voice_channel_class(self):
        assert VoiceChannel is not None
        assert hasattr(VoiceChannel, "connect")

    def test_voice_client_class(self):
        assert VoiceClient is not None
        assert hasattr(VoiceClient, "connect")
        assert hasattr(VoiceClient, "disconnect")
        assert hasattr(VoiceClient, "move")

    def test_voice_client_connect_static(self):
        assert callable(VoiceClient.connect)

    def test_voice_state_re_export(self):
        from sosad.compat.voice import VoiceState
        assert VoiceState is hikari.VoiceState
