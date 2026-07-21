"""Component interaction base types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import hikari


@dataclass(frozen=True, slots=True)
class ComponentContext:
    """Context for a component interaction (button click, select menu, modal submit)."""

    interaction: hikari.ComponentInteraction | hikari.ModalInteraction
    client: Any  # Client
    app: Any  # App

    @property
    def author(self) -> hikari.User:
        return self.interaction.user

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        return self.interaction.guild_id

    @property
    def channel_id(self) -> hikari.Snowflake:
        return self.interaction.channel_id

    @property
    def custom_id(self) -> str:
        return self.interaction.custom_id

    @property
    def values(self) -> list[str]:
        if isinstance(self.interaction, hikari.ComponentInteraction):
            return self.interaction.values
        return []

    @property
    def component_type(self) -> hikari.ComponentType | None:
        if isinstance(self.interaction, hikari.ComponentInteraction):
            return self.interaction.component_type
        return None

    def respond(self) -> Any:
        from sosad.context.context import ResponseBuilder
        return ResponseBuilder(_interaction=self.interaction)


@runtime_checkable
class ButtonHandler(Protocol):
    async def __call__(self, ctx: ComponentContext) -> None: ...


@runtime_checkable
class SelectHandler(Protocol):
    async def __call__(self, ctx: ComponentContext) -> None: ...


@runtime_checkable
class ModalHandler(Protocol):
    async def __call__(self, ctx: ComponentContext) -> None: ...


@dataclass(frozen=True, slots=True)
class ButtonMeta:
    custom_id: str
    handler: Any
    label: str | None = None
    style: hikari.ButtonStyle = hikari.ButtonStyle.SECONDARY
    emoji: str | hikari.Emoji | None = None
    disabled: bool = False
    row: int | None = None


@dataclass(frozen=True, slots=True)
class SelectMeta:
    custom_id: str
    handler: Any
    select_type: hikari.ComponentType = hikari.ComponentType.TEXT_SELECT_MENU
    placeholder: str | None = None
    min_values: int = 1
    max_values: int = 1
    options: tuple[dict[str, Any], ...] = ()
    disabled: bool = False
    row: int | None = None


@dataclass(frozen=True, slots=True)
class ModalMeta:
    custom_id: str
    handler: Any
    title: str = "Modal"
    components: tuple[dict[str, Any], ...] = ()


__all__ = [
    "ButtonHandler",
    "ButtonMeta",
    "ComponentContext",
    "ModalHandler",
    "ModalMeta",
    "SelectHandler",
    "SelectMeta",
]
