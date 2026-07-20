"""Persistent views — views that survive across interactions until timeout."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

import hikari

from sosad.components.view import ButtonBuilder, SelectBuilder

_VIEW_PREFIX = "sv"


class PersistentView:
    """A view that persists across interactions until its timeout expires.

    Unlike ephemeral decorator-based components, PersistentView enables
    stateful interactions: create a view, attach handlers, send it, and
    handle follow-up clicks without re-registering.

    Usage::

        view = PersistentView(timeout=60.0)
        view.button(custom_id="confirm", label="Confirm", style=hikari.ButtonStyle.SUCCESS)
        view.button(custom_id="cancel", label="Cancel", style=hikari.ButtonStyle.DANGER)

        @view.on_click("confirm")
        async def on_confirm(ctx):
            await ctx.respond().content("Confirmed!").send()

        @view.on_click("cancel")
        async def on_cancel(ctx):
            await ctx.respond().content("Cancelled!").send()

        await ctx.respond().components(view).send()
    """

    views: dict[str, PersistentView] = {}

    def __init__(self, timeout: float = 180.0) -> None:
        self.id: str = uuid.uuid4().hex[:12]
        self.timeout = timeout
        self.created_at = time.time()
        self._components: list[ButtonBuilder | SelectBuilder] = []
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._handler_registry: dict[str, Callable[..., Any]] = {}
        PersistentView.views[self.id] = self

    def button(
        self,
        *,
        custom_id: str,
        label: str | None = None,
        style: hikari.ButtonStyle = hikari.ButtonStyle.SECONDARY,
        emoji: str | hikari.Emoji | None = None,
        disabled: bool = False,
        url: str | None = None,
        row: int | None = None,
    ) -> ButtonBuilder:
        actual_id = self._encode_id(custom_id)
        btn = ButtonBuilder(
            custom_id=actual_id,
            label=label,
            style=style,
            emoji=emoji,
            disabled=disabled,
            url=url,
            row=row,
        )
        self._components.append(btn)
        self._handler_registry[custom_id] = None  # placeholder
        return btn

    def select(
        self,
        *,
        custom_id: str,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
    ) -> SelectBuilder:
        actual_id = self._encode_id(custom_id)
        sel = SelectBuilder(
            custom_id=actual_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
        )
        self._components.append(sel)
        self._handler_registry[custom_id] = None
        return sel

    def on_click(self, custom_id: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._handlers[custom_id] = func
            return func
        return decorator

    def on_select(self, custom_id: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._handlers[custom_id] = func
            return func
        return decorator

    def set_handler(self, custom_id: str, handler: Callable[..., Any]) -> None:
        self._handlers[custom_id] = handler

    def get_all_components(self) -> list[ButtonBuilder | SelectBuilder]:
        return self._components

    def build_rows(self) -> list[list[dict[str, Any]]]:
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
        result: dict[str, Callable[..., Any]] = {}
        for comp in self._components:
            cid = comp.custom_id
            if cid and isinstance(cid, str):
                original_id = self._decode_id(cid)
                handler = self._handlers.get(original_id)
                if handler:
                    result[cid] = handler
        return result

    def _encode_id(self, custom_id: str) -> str:
        return f"{_VIEW_PREFIX}:{self.id}:{custom_id}"

    @staticmethod
    def _decode_id(encoded: str) -> str:
        parts = encoded.split(":", 2)
        if len(parts) == 3 and parts[0] == _VIEW_PREFIX:
            return parts[2]
        return encoded

    @staticmethod
    def parse_custom_id(encoded: str) -> tuple[str, str] | None:
        parts = encoded.split(":", 2)
        if len(parts) == 3 and parts[0] == _VIEW_PREFIX:
            return parts[1], parts[2]
        return None

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.timeout

    async def on_timeout(self) -> None:
        pass

    @classmethod
    def cleanup_expired(cls) -> None:
        now = time.time()
        expired = [
            vid for vid, v in list(cls.views.items())
            if now - v.created_at > v.timeout
        ]
        for vid in expired:
            view = cls.views.pop(vid, None)
            if view is not None:
                import asyncio
                asyncio.ensure_future(view.on_timeout())

    @classmethod
    def get_view(cls, view_id: str) -> PersistentView | None:
        return cls.views.get(view_id)


__all__ = ["PersistentView"]
