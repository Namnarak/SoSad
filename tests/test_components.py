"""Tests for the component system."""

import hikari

from sosad.components.base import ButtonMeta, ComponentContext, ModalMeta, SelectMeta
from sosad.components.decorators import button, modal, select
from sosad.components.registry import ComponentRegistry


def test_button_decorator():
    @button("my_btn", label="Click Me", style=hikari.ButtonStyle.PRIMARY)
    async def on_click(ctx): ...

    assert isinstance(on_click, ButtonMeta)
    assert on_click.custom_id == "my_btn"
    assert on_click.label == "Click Me"
    assert on_click.style == hikari.ButtonStyle.PRIMARY


def test_select_decorator():
    @select("my_select", placeholder="Pick one", options=[
        {"label": "A", "value": "a"},
        {"label": "B", "value": "b"},
    ])
    async def on_select(ctx): ...

    assert isinstance(on_select, SelectMeta)
    assert on_select.custom_id == "my_select"
    assert on_select.placeholder == "Pick one"
    assert len(on_select.options) == 2


def test_modal_decorator():
    @modal("my_modal", title="My Form")
    async def on_submit(ctx): ...

    assert isinstance(on_submit, ModalMeta)
    assert on_submit.custom_id == "my_modal"
    assert on_submit.title == "My Form"


def test_registry_add_and_resolve():
    reg = ComponentRegistry()
    meta = ButtonMeta(custom_id="test", handler=lambda: None)
    reg.add_button(meta)
    assert reg.resolve_button("test") is meta
    assert reg.resolve_button("nonexistent") is None
    assert reg.count == 1


def test_registry_remove():
    reg = ComponentRegistry()
    reg.add_button(ButtonMeta(custom_id="a", handler=lambda: None))
    reg.add_select(SelectMeta(custom_id="b", handler=lambda: None))
    assert reg.remove("a") is True
    assert reg.remove("b") is True
    assert reg.remove("c") is False
    assert reg.count == 0


def test_component_context_custom_id():
    from unittest.mock import MagicMock

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
