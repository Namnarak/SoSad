"""Paginator — page navigation built on PersistentView."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import hikari

from sosad.components.persistent import PersistentView
from sosad.components.view import ButtonBuilder

_PREV = "◀"
_NEXT = "▶"
_FIRST = "⏪"
_LAST = "⏩"
_STOP = "⏹"
_PAGE_INDICATOR = "📄"


class Paginator(PersistentView):
    """A paginated view that renders pages with navigation controls.

    Usage::

        pages = ["Page 1", "Page 2", "Page 3"]

        paginator = Paginator(pages, timeout=60.0)

        @paginator.on_click("prev")
        async def on_prev(ctx):
            paginator.current -= 1
            await ctx.respond().content(paginator.current_page).send()

        @paginator.on_click("next")
        async def on_next(ctx):
            paginator.current += 1
            await ctx.respond().content(paginator.current_page).send()

        await ctx.respond().components(paginator).send()

    Simplified usage with auto-render::

        paginator = Paginator(pages, renderer=lambda p: p)
        await ctx.respond().components(paginator).send()
        # navigation handlers are auto-wired
    """

    def __init__(
        self,
        pages: list[Any],
        *,
        timeout: float = 180.0,
        renderer: Callable[[Any], Any] | None = None,
        show_first_last: bool = True,
        show_stop: bool = False,
        auto_wire: bool = True,
        page_range_size: int | None = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.pages = pages
        self._current_page = 0
        self._renderer = renderer or (lambda p: p)
        self._show_first_last = show_first_last
        self._auto_wired = False
        self._page_range_size = page_range_size

        if auto_wire:
            self._add_nav_buttons(show_first_last, show_stop)
            self._wire_nav_handlers()

    def _add_nav_buttons(
        self,
        show_first_last: bool,
        show_stop: bool,
    ) -> None:
        if show_first_last:
            self.button(custom_id="first", label=_FIRST, style=hikari.ButtonStyle.SECONDARY)
        self.button(custom_id="prev", label=_PREV, style=hikari.ButtonStyle.PRIMARY)
        self.button(
            custom_id="page_indicator",
            label=_PAGE_INDICATOR,
            style=hikari.ButtonStyle.SECONDARY,
            disabled=True,
        )
        self.button(custom_id="next", label=_NEXT, style=hikari.ButtonStyle.PRIMARY)
        if show_first_last:
            self.button(custom_id="last", label=_LAST, style=hikari.ButtonStyle.SECONDARY)
        if show_stop:
            self.button(custom_id="stop", label=_STOP, style=hikari.ButtonStyle.DANGER)

    def _wire_nav_handlers(self) -> None:
        self.set_handler("first", self._on_first)
        self.set_handler("prev", self._on_prev)
        self.set_handler("next", self._on_next)
        self.set_handler("last", self._on_last)
        self.set_handler("stop", self._on_stop)
        self._auto_wired = True

    @property
    def current_page(self) -> Any:
        if 0 <= self._current_page < len(self.pages):
            return self._renderer(self.pages[self._current_page])
        return self._renderer(self.pages[0])

    @property
    def current_page_data(self) -> Any:
        if 0 <= self._current_page < len(self.pages):
            return self.pages[self._current_page]
        return self.pages[0] if self.pages else None

    @property
    def total(self) -> int:
        return len(self.pages)

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def can_prev(self) -> bool:
        return self._current_page > 0

    @property
    def can_next(self) -> bool:
        return self._current_page < len(self.pages) - 1

    @property
    def is_first_page(self) -> bool:
        return self._current_page == 0

    @property
    def is_last_page(self) -> bool:
        return self._current_page >= len(self.pages) - 1

    @property
    def page_range(self) -> tuple[int, int]:
        if self._page_range_size is None:
            return (0, len(self.pages) - 1) if self.pages else (0, 0)
        start = (self._current_page // self._page_range_size) * self._page_range_size
        end = min(start + self._page_range_size - 1, len(self.pages) - 1)
        return (start, end)

    def next_page(self) -> None:
        if self.can_next:
            self._current_page += 1

    def previous_page(self) -> None:
        if self.can_prev:
            self._current_page -= 1

    def first_page(self) -> None:
        self._current_page = 0

    def last_page(self) -> None:
        self._current_page = len(self.pages) - 1

    def go_to_page(self, page: int) -> None:
        self._current_page = max(0, min(page, len(self.pages) - 1))

    def update_page_indicator(self) -> None:
        for comp in self._components:
            if isinstance(comp, ButtonBuilder) and comp.custom_id \
                    and "page_indicator" in comp.custom_id:
                comp.label = f"{self._current_page + 1}/{self.total}"
                break

    async def _on_first(self, ctx: Any) -> None:
        self._current_page = 0
        self.update_page_indicator()
        await self._update_message(ctx)

    async def _on_prev(self, ctx: Any) -> None:
        if self.can_prev:
            self._current_page -= 1
        self.update_page_indicator()
        await self._update_message(ctx)

    async def _on_next(self, ctx: Any) -> None:
        if self.can_next:
            self._current_page += 1
        self.update_page_indicator()
        await self._update_message(ctx)

    async def _on_last(self, ctx: Any) -> None:
        self._current_page = len(self.pages) - 1
        self.update_page_indicator()
        await self._update_message(ctx)

    async def _on_stop(self, ctx: Any) -> None:
        PersistentView.views.pop(self.id, None)

    async def _update_message(self, ctx: Any) -> None:
        content = self.current_page
        if isinstance(content, str):
            builder = ctx.respond().content(content)
        elif isinstance(content, hikari.Embed):
            builder = ctx.respond().embed(content)
        else:
            builder = ctx.respond().content(str(content))
        await builder.components(self).send()


__all__ = ["Paginator"]
