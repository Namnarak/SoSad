"""Decorator-based component registration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import hikari

from sosad.components.base import ButtonMeta, ModalMeta, SelectMeta
from sosad.components.registry import get_component_registry


def button(
    custom_id: str,
    *,
    label: str | None = None,
    style: hikari.ButtonStyle = hikari.ButtonStyle.SECONDARY,
    emoji: str | hikari.Emoji | None = None,
    disabled: bool = False,
    row: int | None = None,
) -> Callable[[Any], ButtonMeta]:
    """Decorator that registers a button interaction handler.

    Usage::

        @sosad.button("confirm", label="Confirm", style=hikari.ButtonStyle.SUCCESS)
        async def on_confirm(ctx: ComponentContext) -> None:
            await ctx.respond().content("Confirmed!").ephemeral().send()
    """

    def decorator(func: Any) -> ButtonMeta:
        meta = ButtonMeta(
            custom_id=custom_id,
            handler=func,
            label=label,
            style=style,
            emoji=emoji,
            disabled=disabled,
            row=row,
        )
        get_component_registry().add_button(meta)
        return meta

    return decorator


def select(
    custom_id: str,
    *,
    select_type: hikari.ComponentType = hikari.ComponentType.TEXT_SELECT_MENU,
    placeholder: str | None = None,
    min_values: int = 1,
    max_values: int = 1,
    options: list[dict[str, Any]] | None = None,
    disabled: bool = False,
    row: int | None = None,
) -> Callable[[Any], SelectMeta]:
    """Decorator that registers a select menu interaction handler.

    Usage::

        @sosad.select("color_picker", placeholder="Pick a color", options=[
            {"label": "Red", "value": "red"},
            {"label": "Blue", "value": "blue"},
        ])
        async def on_color(ctx: ComponentContext) -> None:
            color = ctx.values[0]
            await ctx.respond().content(f"You picked {color}!").send()
    """

    def decorator(func: Any) -> SelectMeta:
        meta = SelectMeta(
            custom_id=custom_id,
            handler=func,
            select_type=select_type,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=tuple(options) if options else (),
            disabled=disabled,
            row=row,
        )
        get_component_registry().add_select(meta)
        return meta

    return decorator


def modal(
    custom_id: str,
    *,
    title: str = "Modal",
    components: list[dict[str, Any]] | None = None,
) -> Callable[[Any], ModalMeta]:
    """Decorator that registers a modal submission handler.

    Usage::

        @sosad.modal("feedback_form", title="Feedback")
        async def on_feedback(ctx: ComponentContext) -> None:
            # Modal text inputs are in interaction.components
            await ctx.respond().content("Thanks!").ephemeral().send()
    """

    def decorator(func: Any) -> ModalMeta:
        meta = ModalMeta(
            custom_id=custom_id,
            handler=func,
            title=title,
            components=tuple(components) if components else (),
        )
        get_component_registry().add_modal(meta)
        return meta

    return decorator


__all__ = ["button", "modal", "select"]
