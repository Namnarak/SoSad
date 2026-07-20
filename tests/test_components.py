"""Tests for the component system."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import hikari
import pytest

from sosad.components.base import ButtonMeta, ComponentContext, ModalMeta, SelectMeta
from sosad.components.decorators import button, modal, select
from sosad.components.registry import ComponentRegistry
from sosad.components.view import View, ButtonBuilder, SelectBuilder
from sosad.components.modal import TextInputBuilder


class TestButtonDecorator:
    def test_basic(self):
        @button("my_btn", label="Click Me", style=hikari.ButtonStyle.PRIMARY)
        async def on_click(ctx): ...

        assert isinstance(on_click, ButtonMeta)
        assert on_click.custom_id == "my_btn"
        assert on_click.label == "Click Me"
        assert on_click.style == hikari.ButtonStyle.PRIMARY

    def test_default_style(self):
        @button("btn", label="Default")
        async def fn(ctx): ...
        assert fn.style == hikari.ButtonStyle.SECONDARY

    def test_with_emoji(self):
        @button("emoji_btn", label="With Emoji", emoji="👍")
        async def fn(ctx): ...
        assert fn.emoji == "👍"

    def test_disabled(self):
        @button("disabled", label="Disabled", disabled=True)
        async def fn(ctx): ...
        assert fn.disabled is True

    def test_with_emoji_style(self):
        @button("styled", label="Styled", style=hikari.ButtonStyle.SUCCESS)
        async def fn(ctx): ...
        assert fn.style == hikari.ButtonStyle.SUCCESS

    def test_row(self):
        @button("row_btn", label="Row 2", row=2)
        async def fn(ctx): ...
        assert fn.row == 2


class TestSelectDecorator:
    def test_basic(self):
        @select("my_select", placeholder="Pick one", options=[
            {"label": "A", "value": "a"},
            {"label": "B", "value": "b"},
        ])
        async def on_select(ctx): ...

        assert isinstance(on_select, SelectMeta)
        assert on_select.custom_id == "my_select"
        assert on_select.placeholder == "Pick one"
        assert len(on_select.options) == 2

    def test_min_max_values(self):
        @select("multi", placeholder="Pick", options=[{"label": "A", "value": "a"}],
                min_values=1, max_values=3)
        async def fn(ctx): ...
        assert fn.min_values == 1
        assert fn.max_values == 3

    def test_disabled(self):
        @select("disabled", placeholder="Nope", options=[{"label": "A", "value": "a"}],
                disabled=True)
        async def fn(ctx): ...
        assert fn.disabled is True


class TestModalDecorator:
    def test_basic(self):
        @modal("my_modal", title="My Form")
        async def on_submit(ctx): ...

        assert isinstance(on_submit, ModalMeta)
        assert on_submit.custom_id == "my_modal"
        assert on_submit.title == "My Form"

    def test_with_components(self):
        @modal("complex", title="Complex Form")
        async def on_submit(ctx): ...

        assert on_submit.custom_id == "complex"
        assert on_submit.title == "Complex Form"


class TestComponentRegistry:
    def test_add_and_resolve(self):
        reg = ComponentRegistry()
        meta = ButtonMeta(custom_id="test", handler=lambda: None)
        reg.add_button(meta)
        assert reg.resolve_button("test") is meta
        assert reg.resolve_button("nonexistent") is None

    def test_count(self):
        reg = ComponentRegistry()
        assert reg.count == 0
        reg.add_button(ButtonMeta(custom_id="a", handler=lambda: None))
        reg.add_select(SelectMeta(custom_id="b", handler=lambda: None))
        assert reg.count == 2

    def test_remove(self):
        reg = ComponentRegistry()
        reg.add_button(ButtonMeta(custom_id="a", handler=lambda: None))
        reg.add_select(SelectMeta(custom_id="b", handler=lambda: None))
        assert reg.remove("a") is True
        assert reg.remove("b") is True
        assert reg.remove("c") is False
        assert reg.count == 0

    def test_get_handler(self):
        reg = ComponentRegistry()
        async def handler(ctx): ...
        meta = ButtonMeta(custom_id="test", handler=handler)
        reg.add_button(meta)
        assert reg.get_handler("test") is handler
        assert reg.get_handler("nope") is None

    def test_get_modal_handler(self):
        reg = ComponentRegistry()
        async def handler(ctx): ...
        meta = ModalMeta(custom_id="modal_test", handler=handler)
        reg.add_modal(meta)
        assert reg.get_modal_handler("modal_test") is handler

    def test_get_instance(self):
        reg1 = ComponentRegistry.get_instance()
        reg2 = ComponentRegistry.get_instance()
        assert reg1 is reg2

class TestComponentContext:
    def test_custom_id(self):
        mock_interaction = MagicMock(spec=hikari.ComponentInteraction)
        mock_interaction.custom_id = "btn_123"
        mock_interaction.user = MagicMock()
        mock_interaction.guild_id = None
        mock_interaction.channel_id = hikari.Snowflake(123)
        mock_interaction.values = ["red"]
        mock_interaction.component_type = hikari.ComponentType.BUTTON

        ctx = ComponentContext(
            interaction=mock_interaction,
            client=MagicMock(),
            app=MagicMock(),
        )
        assert ctx.custom_id == "btn_123"
        assert ctx.values == ["red"]
        assert ctx.component_type == hikari.ComponentType.BUTTON

    def test_author(self):
        mock_interaction = MagicMock(spec=hikari.ComponentInteraction)
        mock_interaction.user = MagicMock()
        mock_interaction.user.id = 12345
        mock_interaction.custom_id = "test"
        mock_interaction.guild_id = None
        mock_interaction.channel_id = hikari.Snowflake(1)
        mock_interaction.values = []
        mock_interaction.component_type = hikari.ComponentType.BUTTON

        ctx = ComponentContext(
            interaction=mock_interaction,
            client=MagicMock(),
            app=MagicMock(),
        )
        assert ctx.author.id == 12345


class TestButtonBuilder:
    def test_create_button(self):
        btn = ButtonBuilder(custom_id="test", label="Test")
        assert btn.custom_id == "test"
        assert btn.label == "Test"
        assert btn.style == hikari.ButtonStyle.SECONDARY

    def test_styles(self):
        assert hikari.ButtonStyle.PRIMARY is not None
        assert hikari.ButtonStyle.SECONDARY is not None
        assert hikari.ButtonStyle.SUCCESS is not None
        assert hikari.ButtonStyle.DANGER is not None
        assert hikari.ButtonStyle.LINK is not None


class TestView:
    def test_create_view(self):
        view = View()
        assert len(view._components) == 0

    def test_button(self):
        view = View()
        view.button(custom_id="test", label="Test Button", style=hikari.ButtonStyle.PRIMARY)
        assert len(view._components) == 1
        assert view._components[0].custom_id == "test"

    def test_select(self):
        view = View()
        view.select(custom_id="test_select", placeholder="Pick")
        assert len(view._components) == 1
        assert view._components[0].custom_id == "test_select"

    def test_button_with_url(self):
        view = View()
        view.button(custom_id="link", label="Click", url="https://example.com")
        assert len(view._components) == 1
        assert view._components[0].url == "https://example.com"

    def test_multiple_components(self):
        view = View()
        view.button(custom_id="a", label="A", style=hikari.ButtonStyle.PRIMARY)
        view.select(custom_id="b", placeholder="B")
        assert len(view._components) == 2

    def test_build_rows(self):
        view = View()
        view.button(custom_id="a", label="A", style=hikari.ButtonStyle.PRIMARY)
        view.button(custom_id="b", label="B", style=hikari.ButtonStyle.SECONDARY)
        rows = view.build_rows()
        assert len(rows) >= 1


class TestSelectBuilder:
    def test_create_select(self):
        options = [("A", "a"), ("B", "b")]
        select = SelectBuilder(custom_id="test", placeholder="Pick", options=options)
        assert select.custom_id == "test"
        assert len(select.options) == 2

    def test_min_max(self):
        select = SelectBuilder(custom_id="test", placeholder="Pick",
                                options=[("A", "a")], min_values=1, max_values=5)
        assert select.min_values == 1
        assert select.max_values == 5


class TestTextInputBuilder:
    def test_create_input(self):
        inp = TextInputBuilder(custom_id="name", label="Your name")
        assert inp.custom_id == "name"
        assert inp.label == "Your name"
        assert inp.style == hikari.TextInputStyle.SHORT

    def test_paragraph_style(self):
        inp = TextInputBuilder(custom_id="msg", label="Message",
                               style=hikari.TextInputStyle.PARAGRAPH)
        assert inp.style == hikari.TextInputStyle.PARAGRAPH
