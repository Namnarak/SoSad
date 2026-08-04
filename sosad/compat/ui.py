"""Class-based ``discord.ui`` compatibility built on SoSad components."""

from __future__ import annotations

import asyncio
import inspect
import uuid
from collections.abc import Callable, Iterable
from typing import Any

import hikari

from sosad.compat.types import ButtonStyle, SelectOption, TextStyle


def _component_id(prefix: str) -> str:
    return f"compat:{prefix}:{uuid.uuid4().hex}"


async def _maybe_await(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


class Item:
    """Base type for interactive UI items."""


class Button(Item):
    """A discord.py-shaped button item."""

    def __init__(
        self,
        *,
        style: hikari.ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: Any = None,
        row: int | None = None,
        callback: Callable[..., Any] | None = None,
    ) -> None:
        self.style = style
        self.label = label
        self.disabled = disabled
        self.custom_id = custom_id or (None if url else _component_id("button"))
        self.url = url
        self.emoji = emoji
        self.row = row
        self.callback = callback
        self.view: View | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": hikari.ComponentType.BUTTON.value,
            "style": self.style.value,
            "disabled": self.disabled,
        }
        if self.custom_id is not None:
            data["custom_id"] = self.custom_id
        if self.url is not None:
            data["url"] = self.url
        if self.label is not None:
            data["label"] = self.label
        if self.emoji is not None:
            data["emoji"] = self.emoji
        return data


class Select(Item):
    """A discord.py-shaped select menu item."""

    def __init__(
        self,
        *,
        custom_id: str | None = None,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int = 1,
        options: Iterable[SelectOption | dict[str, Any]] = (),
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        self.custom_id = custom_id or _component_id("select")
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.options = [
            option if isinstance(option, SelectOption) else SelectOption(**option)
            for option in options
        ]
        self.disabled = disabled
        self.row = row
        self.view: View | None = None
        self.values: list[str] = []

    async def callback(self, interaction: Any) -> None:
        del interaction

    def add_option(
        self,
        *,
        label: str,
        value: str | None = None,
        description: str | None = None,
        emoji: Any = None,
        default: bool = False,
    ) -> Select:
        self.options.append(
            SelectOption(
                label=label,
                value=value or label,
                description=description,
                emoji=emoji,
                default=default,
            )
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": hikari.ComponentType.TEXT_SELECT_MENU.value,
            "custom_id": self.custom_id,
            "placeholder": self.placeholder,
            "min_values": self.min_values,
            "max_values": self.max_values,
            "options": [option.to_dict() for option in self.options],
            "disabled": self.disabled,
        }


class UserSelect(Select):
    """Select menu restricted to users."""


class RoleSelect(Select):
    """Select menu restricted to roles."""


class ChannelSelect(Select):
    """Select menu restricted to channels."""


class MentionableSelect(Select):
    """Select menu accepting users or roles."""


class Label(Item):
    """Container used by Discord's newer modal component layout."""

    def __init__(
        self,
        *,
        text: str,
        component: Item,
        description: str | None = None,
    ) -> None:
        self.text = text
        self.description = description
        self.component = component

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": 18,
            "label": self.text,
            "component": self.component.to_dict(),
        }
        if self.description is not None:
            data["description"] = self.description
        return data


class _ItemSpec:
    def __init__(self, item_type: type[Button] | type[Select], **kwargs: Any) -> None:
        self.item_type = item_type
        self.kwargs = kwargs

    def __call__(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        callback.__discord_ui_item__ = self
        return callback


def button(**kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorate a View callback with a button item."""
    return _ItemSpec(Button, **kwargs)


def select(**kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorate a View callback with a select item."""
    return _ItemSpec(Select, **kwargs)


class _ViewMeta(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> _ViewMeta:
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class View(metaclass=_ViewMeta):
    """A discord.py-compatible view that renders through SoSad's builders."""

    def __init__(self, *, timeout: float | None = 180.0) -> None:
        self.timeout = timeout
        self._children: list[Button | Select] = []
        self._finished = False
        self._waiter = asyncio.Event()

        for cls in reversed(type(self).__mro__):
            for name, member in vars(cls).items():
                spec = getattr(member, "__discord_ui_item__", None)
                if spec is None:
                    continue
                item = spec.item_type(**spec.kwargs)
                item.callback = getattr(self, name)
                self.add_item(item)

    @classmethod
    def from_message(cls, message: Any, *, timeout: float | None = 180.0) -> View:
        del message
        return cls(timeout=timeout)

    @property
    def children(self) -> list[Button | Select]:
        return list(self._children)

    def add_item(self, item: Button | Select) -> View:
        item.view = self
        self._children.append(item)
        return self

    def remove_item(self, item: Button | Select) -> View:
        self._children.remove(item)
        item.view = None
        return self

    def clear_items(self) -> View:
        for item in self._children:
            item.view = None
        self._children.clear()
        return self

    def stop(self) -> None:
        self._finished = True
        self._waiter.set()

    def is_finished(self) -> bool:
        return self._finished

    async def wait(self) -> bool:
        if not self._finished:
            if self.timeout is None:
                await self._waiter.wait()
            else:
                try:
                    await asyncio.wait_for(self._waiter.wait(), self.timeout)
                except TimeoutError:
                    self._finished = True
                    await _maybe_await(self.on_timeout())
        return self._finished

    async def on_timeout(self) -> None:
        return None

    async def on_error(self, interaction: Any, error: Exception, item: Item) -> None:
        del interaction, item
        raise error

    def build_rows(self) -> list[list[dict[str, Any]]]:
        rows: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        for item in self._children:
            data = item.to_dict()
            if isinstance(item, Select) or item.row is not None:
                if current:
                    rows.append(current)
                    current = []
                if item.row is not None:
                    while len(rows) <= item.row:
                        rows.append([])
                    rows[item.row].append(data)
                else:
                    rows.append([data])
            else:
                if len(current) >= 5:
                    rows.append(current)
                    current = []
                current.append(data)
        if current:
            rows.append(current)
        return rows

    def get_handlers(self) -> dict[str, Callable[..., Any]]:
        handlers: dict[str, Callable[..., Any]] = {}
        for item in self._children:
            if item.callback is None or item.custom_id is None:
                continue

            async def dispatch(ctx: Any, _item=item) -> Any:
                interaction = getattr(ctx, "interaction", ctx)
                if (
                    isinstance(_item, Select)
                    and isinstance(interaction, hikari.ComponentInteraction)
                ):
                    _item.values = list(interaction.values)
                    from sosad.compat.interaction import wrap_interaction

                    return await _maybe_await(
                        _item.callback(wrap_interaction(interaction))
                    )
                from sosad.compat.interaction import wrap_interaction

                return await _maybe_await(
                    _item.callback(wrap_interaction(interaction), _item)
                )

            handlers[item.custom_id] = dispatch
        return handlers


class TextInput:
    """Declarative modal text input."""

    def __init__(
        self,
        *,
        label: str,
        custom_id: str | None = None,
        style: hikari.TextInputStyle = TextStyle.short,
        placeholder: str | None = None,
        default: str | None = None,
        required: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.label = label
        self.custom_id = custom_id or _component_id("input")
        self.style = style
        self.placeholder = placeholder
        self.default = default
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.value = default or ""

    def clone(self) -> TextInput:
        return TextInput(
            label=self.label,
            custom_id=self.custom_id,
            style=self.style,
            placeholder=self.placeholder,
            default=self.default,
            required=self.required,
            min_length=self.min_length,
            max_length=self.max_length,
        )

    def __str__(self) -> str:
        return self.value

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": hikari.ComponentType.TEXT_INPUT.value,
            "custom_id": self.custom_id,
            "style": self.style.value,
            "label": self.label,
            "required": self.required,
        }
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        if self.default is not None:
            data["value"] = self.default
        if self.min_length is not None:
            data["min_length"] = self.min_length
        if self.max_length is not None:
            data["max_length"] = self.max_length
        return data


class _ModalMeta(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> _ModalMeta:
        title = kwargs.pop("title", None)
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        if title is not None:
            cls.__modal_title__ = title
        return cls


class Modal(metaclass=_ModalMeta):
    """Declarative discord.py-compatible modal."""

    __modal_title__ = "Modal"

    def __init__(
        self,
        *,
        title: str | None = None,
        timeout: float | None = None,
        custom_id: str | None = None,
    ) -> None:
        self.title = title or self.__modal_title__
        self.timeout = timeout
        self.custom_id = custom_id or _component_id("modal")
        self.interaction: Any = None
        self._finished = False
        self._waiter = asyncio.Event()
        self._children: list[Item] = []
        for cls in reversed(type(self).__mro__):
            for name, member in vars(cls).items():
                if isinstance(member, TextInput):
                    value = member.clone()
                    setattr(self, name, value)

    def add_item(self, item: Item) -> Modal:
        self._children.append(item)
        return self

    def walk_children(self) -> Iterable[Item]:
        for item in self._children:
            yield item
            component = getattr(item, "component", None)
            if isinstance(component, Item):
                yield component

    async def on_submit(self, interaction: Any) -> None:
        del interaction

    def stop(self) -> None:
        self._finished = True
        self._waiter.set()

    def is_finished(self) -> bool:
        return self._finished

    async def wait(self) -> bool:
        if not self._finished:
            await self._waiter.wait()
        return self._finished

    def build(self) -> dict[str, Any]:
        components = [
            {"type": hikari.ComponentType.ACTION_ROW.value, "components": [item.to_dict()]}
            for item in self._inputs()
        ]
        return {"title": self.title, "custom_id": self.custom_id, "components": components}

    def _inputs(self) -> list[TextInput]:
        return [
            value
            for value in vars(self).values()
            if isinstance(value, TextInput)
        ]

    @property
    def handler(self) -> Callable[..., Any]:
        async def dispatch(ctx: Any) -> Any:
            from sosad.compat.interaction import wrap_interaction

            interaction = wrap_interaction(getattr(ctx, "interaction", ctx))
            self.interaction = interaction
            return await _maybe_await(self.on_submit(interaction))

        return dispatch


__all__ = [
    "Button",
    "ChannelSelect",
    "Item",
    "Label",
    "MentionableSelect",
    "Modal",
    "RoleSelect",
    "Select",
    "SelectOption",
    "TextInput",
    "UserSelect",
    "View",
    "button",
    "select",
]
