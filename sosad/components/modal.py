"""Modal builder for building modals dynamically."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import hikari


@dataclass
class TextInputBuilder:
    """Builder for a text input component in a modal."""

    custom_id: str
    style: hikari.TextInputStyle = hikari.TextInputStyle.SHORT
    label: str = ""
    placeholder: str | None = None
    default: str | None = None
    required: bool = True
    min_length: int | None = None
    max_length: int | None = None

    def set_label(self, label: str) -> TextInputBuilder:
        self.label = label
        return self

    def set_style(self, style: hikari.TextInputStyle) -> TextInputBuilder:
        self.style = style
        return self

    def set_placeholder(self, placeholder: str) -> TextInputBuilder:
        self.placeholder = placeholder
        return self

    def set_default(self, default: str) -> TextInputBuilder:
        self.default = default
        return self

    def set_required(self, required: bool = True) -> TextInputBuilder:
        self.required = required
        return self

    def set_min_length(self, min_length: int) -> TextInputBuilder:
        self.min_length = min_length
        return self

    def set_max_length(self, max_length: int) -> TextInputBuilder:
        self.max_length = max_length
        return self

    def build(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": hikari.ComponentType.TEXT_INPUT.value,
            "custom_id": self.custom_id,
            "style": self.style.value,
            "label": self.label,
            "required": self.required,
        }
        if self.placeholder:
            data["placeholder"] = self.placeholder
        if self.default:
            data["value"] = self.default
        if self.min_length is not None:
            data["min_length"] = self.min_length
        if self.max_length is not None:
            data["max_length"] = self.max_length
        return data


class Modal:
    """Builder for modals.

    Usage::

        modal = sosad.Modal(title="Feedback")
        modal.text_input("name", label="Your Name")
        modal.text_input("bio", label="Bio", style=hikari.TextInputStyle.PARAGRAPH)
        await ctx.respond().modal(modal).send()

        # Or with handler:
        modal = sosad.Modal(title="Feedback", on_submit=my_handler)
        modal.text_input("name", label="Your Name")
    """

    def __init__(
        self,
        *,
        title: str = "Modal",
        custom_id: str | None = None,
        on_submit: Callable[..., Any] | None = None,
    ) -> None:
        self._title = title
        self._custom_id = custom_id or f"modal_{uuid.uuid4().hex}"
        self._inputs: list[TextInputBuilder] = []
        self._handler = on_submit

    def text_input(
        self,
        custom_id: str,
        *,
        label: str = "",
        style: hikari.TextInputStyle = hikari.TextInputStyle.SHORT,
        placeholder: str | None = None,
        default: str | None = None,
        required: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> TextInputBuilder:
        inp = TextInputBuilder(
            custom_id=custom_id,
            style=style,
            label=label,
            placeholder=placeholder,
            default=default,
            required=required,
            min_length=min_length,
            max_length=max_length,
        )
        self._inputs.append(inp)
        return inp

    def on_submit(self, handler: Callable[..., Any]) -> Modal:
        self._handler = handler
        return self

    def build(self) -> dict[str, Any]:
        """Build modal data for sending."""
        components: list[dict[str, Any]] = []
        for inp in self._inputs:
            components.append({
                "type": 1,  # ACTION_ROW
                "components": [inp.build()],
            })
        return {
            "title": self._title,
            "custom_id": self._custom_id,
            "components": components,
        }

    @property
    def custom_id(self) -> str:
        return self._custom_id

    @property
    def handler(self) -> Callable[..., Any] | None:
        return self._handler


__all__ = ["Modal", "TextInputBuilder"]
