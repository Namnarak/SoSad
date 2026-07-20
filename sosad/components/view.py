"""View builder for building component layouts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import hikari


@dataclass
class ButtonBuilder:
    """Builder for a single button component."""

    custom_id: str | None = None
    label: str | None = None
    style: hikari.ButtonStyle = hikari.ButtonStyle.SECONDARY
    emoji: str | hikari.Emoji | None = None
    disabled: bool = False
    url: str | None = None
    row: int | None = None
    handler: Callable[..., Any] | None = None

    def set_custom_id(self, custom_id: str) -> ButtonBuilder:
        self.custom_id = custom_id
        return self

    def set_label(self, label: str) -> ButtonBuilder:
        self.label = label
        return self

    def set_style(self, style: hikari.ButtonStyle) -> ButtonBuilder:
        self.style = style
        return self

    def set_emoji(self, emoji: str | hikari.Emoji) -> ButtonBuilder:
        self.emoji = emoji
        return self

    def set_disabled(self, disabled: bool = True) -> ButtonBuilder:
        self.disabled = disabled
        return self

    def set_url(self, url: str) -> ButtonBuilder:
        self.url = url
        return self

    def set_row(self, row: int) -> ButtonBuilder:
        self.row = row
        return self

    def on_click(self, handler: Callable[..., Any]) -> ButtonBuilder:
        self.handler = handler
        return self

    def build(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": hikari.ComponentType.BUTTON.value,
            "style": self.style.value,
        }
        if self.custom_id:
            data["custom_id"] = self.custom_id
        if self.label:
            data["label"] = self.label
        if self.emoji:
            data["emoji"] = self.emoji
        if self.url:
            data["url"] = self.url
        data["disabled"] = self.disabled
        return data


@dataclass
class SelectOptionBuilder:
    """Builder for a single select menu option."""

    label: str
    value: str
    description: str | None = None
    emoji: str | hikari.Emoji | None = None
    default: bool = False

    def build(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "label": self.label,
            "value": self.value,
        }
        if self.description:
            data["description"] = self.description
        if self.emoji:
            data["emoji"] = self.emoji
        if self.default:
            data["default"] = True
        return data


@dataclass
class SelectBuilder:
    """Builder for a select menu component."""

    custom_id: str | None = None
    placeholder: str | None = None
    min_values: int = 1
    max_values: int = 1
    options: list[SelectOptionBuilder] = field(default_factory=list)
    disabled: bool = False
    row: int | None = None
    handler: Callable[..., Any] | None = None

    def set_custom_id(self, custom_id: str) -> SelectBuilder:
        self.custom_id = custom_id
        return self

    def set_placeholder(self, placeholder: str) -> SelectBuilder:
        self.placeholder = placeholder
        return self

    def set_min_values(self, min_values: int) -> SelectBuilder:
        self.min_values = min_values
        return self

    def set_max_values(self, max_values: int) -> SelectBuilder:
        self.max_values = max_values
        return self

    def add_option(
        self,
        label: str,
        value: str,
        *,
        description: str | None = None,
    ) -> SelectBuilder:
        self.options.append(
            SelectOptionBuilder(label=label, value=value, description=description)
        )
        return self

    def set_disabled(self, disabled: bool = True) -> SelectBuilder:
        self.disabled = disabled
        return self

    def set_row(self, row: int) -> SelectBuilder:
        self.row = row
        return self

    def on_select(self, handler: Callable[..., Any]) -> SelectBuilder:
        self.handler = handler
        return self

    def build(self) -> dict[str, Any]:
        return {
            "type": hikari.ComponentType.TEXT_SELECT_MENU.value,
            "custom_id": self.custom_id or "",
            "placeholder": self.placeholder,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "options": [opt.build() for opt in self.options],
            "disabled": self.disabled,
        }


class View:
    """Builder for a set of components (buttons, selects).

    Usage::

        view = sosad.View()
        view.button(label="Yes", style=hikari.ButtonStyle.SUCCESS, custom_id="yes")
        view.button(label="No", style=hikari.ButtonStyle.DANGER, custom_id="no")
        await ctx.respond("Confirm?").components(view).send()
    """

    def __init__(self) -> None:
        self._components: list[ButtonBuilder | SelectBuilder] = []
        self._handlers: dict[str, Callable[..., Any]] = {}

    def button(
        self,
        *,
        custom_id: str | None = None,
        label: str | None = None,
        style: hikari.ButtonStyle = hikari.ButtonStyle.SECONDARY,
        emoji: str | hikari.Emoji | None = None,
        disabled: bool = False,
        url: str | None = None,
    ) -> ButtonBuilder:
        btn = ButtonBuilder(
            custom_id=custom_id,
            label=label,
            style=style,
            emoji=emoji,
            disabled=disabled,
            url=url,
        )
        self._components.append(btn)
        return btn

    def select(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
    ) -> SelectBuilder:
        sel = SelectBuilder(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
        )
        self._components.append(sel)
        return sel

    def build_rows(self) -> list[list[dict[str, Any]]]:
        """Build components into Discord action rows."""
        rows: list[list[dict[str, Any]]] = []
        current_row: list[dict[str, Any]] = []

        for comp in self._components:
            if isinstance(comp, SelectBuilder):
                if current_row:
                    rows.append(current_row)
                    current_row = []
                rows.append([comp.build()])
            elif isinstance(comp, ButtonBuilder):
                if comp.row is not None:
                    while len(rows) <= comp.row:
                        rows.append([])
                    rows[comp.row].append(comp.build())
                else:
                    if len(current_row) >= 5:
                        rows.append(current_row)
                        current_row = []
                    current_row.append(comp.build())

        if current_row:
            rows.append(current_row)

        return rows

    def get_handlers(self) -> dict[str, Callable[..., Any]]:
        handlers: dict[str, Callable[..., Any]] = {}
        for comp in self._components:
            if isinstance(comp, ButtonBuilder) and comp.handler and comp.custom_id:
                handlers[comp.custom_id] = comp.handler
            elif isinstance(comp, SelectBuilder) and comp.handler and comp.custom_id:
                handlers[comp.custom_id] = comp.handler
        return handlers


__all__ = [
    "ButtonBuilder",
    "SelectBuilder",
    "SelectOptionBuilder",
    "View",
]
