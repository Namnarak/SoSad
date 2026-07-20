"""Immutable interaction context and response builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

import hikari

if TYPE_CHECKING:
    from sosad.core.app import App
    from sosad.core.base_client import BaseClient


_MISSING = object()


def _resolve_components(components: tuple[Any, ...]) -> list[Any]:
    """Convert sosad View objects in components to hikari ComponentBuilder objects."""
    from hikari.impl import MessageActionRowBuilder

    resolved: list[Any] = []
    for comp in components:
        if hasattr(comp, "build_rows"):
            rows_data = comp.build_rows()
            for row_dicts in rows_data:
                row = MessageActionRowBuilder()
                for cd in row_dicts:
                    _add_to_row(row, cd)
                resolved.append(row)
        else:
            resolved.append(comp)
    return resolved


def _add_to_row(row: Any, cd: dict[str, Any]) -> None:
    ctype = cd.get("type")
    if ctype == 2:
        url = cd.get("url")
        if url:
            row.add_link_button(url=url, label=cd.get("label"), emoji=cd.get("emoji"))
        else:
            row.add_interactive_button(
                style=cd["style"],
                custom_id=cd.get("custom_id", ""),
                label=cd.get("label"),
                emoji=cd.get("emoji"),
                is_disabled=cd.get("disabled", False),
            )
    elif ctype == 3:
        menu = row.add_text_menu(
            custom_id=cd.get("custom_id", ""),
            placeholder=cd.get("placeholder"),
            min_values=cd.get("min_values", 0),
            max_values=cd.get("max_values", 1),
            is_disabled=cd.get("disabled", False),
        )
        for opt in cd.get("options", []):
            menu.add_option(
                label=opt["label"],
                value=opt["value"],
                description=opt.get("description"),
                emoji=opt.get("emoji"),
                is_default=opt.get("default", False),
            )


def _build_modal_rows(components_data: list[dict[str, Any]]) -> list[Any]:
    """Convert modal component data dicts to hikari ModalActionRowBuilder objects."""
    from hikari.impl import ModalActionRowBuilder

    rows: list[Any] = []
    for item in components_data:
        if item.get("type") != 1:
            continue
        row = ModalActionRowBuilder()
        for child in item.get("components", []):
            if child.get("type") == 4:
                row.add_text_input(
                    custom_id=child.get("custom_id", ""),
                    label=child.get("label", ""),
                    style=child.get("style", 1),
                    placeholder=child.get("placeholder"),
                    value=child.get("value"),
                    required=child.get("required", True),
                    min_length=child.get("min_length", 0),
                    max_length=child.get("max_length", 4000),
                )
        rows.append(row)
    return rows


InteractionT = (
    hikari.CommandInteraction
    | hikari.ComponentInteraction
    | hikari.ModalInteraction
    | hikari.AutocompleteInteraction
)


@dataclass(frozen=True, slots=True)
class ResponseBuilder:
    """Immutable builder for interaction responses. Each method returns a new builder.

    Works with both Gateway and REST modes — uses hikari's built-in
    ``create_initial_response()`` which handles transport internally.
    """

    _interaction: hikari.CommandInteraction | hikari.ComponentInteraction | hikari.ModalInteraction
    _response_type: hikari.ResponseType = hikari.ResponseType.MESSAGE_CREATE
    _content: str | None = None
    _embeds: tuple[hikari.Embed, ...] = ()
    _files: tuple[hikari.File, ...] = ()
    _flags: hikari.MessageFlag = hikari.MessageFlag.NONE
    _components: tuple[Any, ...] = ()
    _modal: Any = None

    def __await__(self) -> Any:
        return self.send().__await__()

    def components(self, *components: Any) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags,
            _components=components,
            _modal=self._modal,
        )

    def modal(self, modal: Any) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
            _modal=modal,
        )

    def content(self, text: str) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=text,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
            _modal=self._modal,
        )

    def embed(self, embed: hikari.Embed) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=(*self._embeds, embed),
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
            _modal=self._modal,
        )

    def embeds(self, *embeds: hikari.Embed) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=(*self._embeds, *embeds),
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
            _modal=self._modal,
        )

    def file(self, file: hikari.File) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=(*self._files, file),
            _flags=self._flags,
            _components=self._components,
            _modal=self._modal,
        )

    def files(self, *files: hikari.File) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=(*self._files, *files),
            _flags=self._flags,
            _components=self._components,
            _modal=self._modal,
        )

    def ephemeral(self) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags | hikari.MessageFlag.EPHEMERAL,
            _components=self._components,
            _modal=self._modal,
        )

    def flag(self, flag: hikari.MessageFlag) -> Self:
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags | flag,
            _components=self._components,
            _modal=self._modal,
        )

    async def send(self) -> Any:
        if self._modal is not None:
            data = self._modal.build()
            rows = _build_modal_rows(data["components"])
            return await self._interaction.create_modal_response(
                data["title"],
                data["custom_id"],
                components=rows,
            )
        kwargs: dict[str, Any] = {}
        if self._content is not None:
            kwargs["content"] = self._content
        if self._embeds:
            kwargs["embeds"] = self._embeds
        if self._files:
            kwargs["attachments"] = self._files
        if self._components:
            kwargs["components"] = _resolve_components(self._components)
        if self._flags is not hikari.MessageFlag.NONE:
            kwargs["flags"] = self._flags
        return await self._interaction.create_initial_response(
            self._response_type,
            **kwargs,
        )

    async def defer(self, *, ephemeral: bool = False) -> None:
        flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.MessageFlag.NONE
        await self._interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            flags=flags,
        )


@dataclass(frozen=True, slots=True)
class InteractionContext:
    """Immutable snapshot of an interaction. Created once per request.

    Works with both Gateway and REST interactions from hikari.
    """

    interaction: hikari.CommandInteraction | hikari.ComponentInteraction | hikari.ModalInteraction
    client: BaseClient
    app: App

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
    def options(self) -> dict[str, hikari.CommandInteractionOption]:
        if isinstance(self.interaction, hikari.CommandInteraction):
            return {opt.name: opt for opt in (self.interaction.options or ())}
        return {}

    def get_option(self, name: str, default: Any = _MISSING) -> Any:
        if not isinstance(self.interaction, hikari.CommandInteraction):
            if default is _MISSING:
                raise KeyError(f"Option '{name}' not found")
            return default
        opts = self.options
        if name not in opts:
            if default is _MISSING:
                raise KeyError(f"Option '{name}' not found")
            return default
        return opts[name].value

    def get_str(self, name: str) -> str:
        value = self.get_option(name)
        if not isinstance(value, str):
            raise TypeError(f"Option '{name}' is not a string")
        return value

    def get_int(self, name: str) -> int:
        value = self.get_option(name)
        if not isinstance(value, int):
            raise TypeError(f"Option '{name}' is not an int")
        return value

    def get_user(self, name: str) -> hikari.User:
        if not isinstance(self.interaction, hikari.CommandInteraction):
            raise TypeError("Not a command interaction")
        opt = self.options.get(name)
        if opt is None:
            raise KeyError(f"Option '{name}' not found")
        resolved = self.interaction.resolved
        if resolved is None:
            raise RuntimeError("No resolved data available")
        user_id = opt.value
        if not isinstance(user_id, hikari.Snowflake):
            raise TypeError(f"Option '{name}' is not a user snowflake")
        user = resolved.members.get(user_id) or resolved.users.get(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        return user

    def respond(
        self,
        content: str | None = None,
        *,
        ephemeral: bool = False,
    ) -> ResponseBuilder:
        """Create a response. Supports both shortcut and builder patterns.

        Shortcut::

            await ctx.respond("Pong!")

        Builder::

            await (
                ctx.respond()
                .content("Done")
                .ephemeral()
                .embed(embed)
                .send()
            )
        """
        builder = ResponseBuilder(interaction=self.interaction)
        if content is not None:
            builder = builder.content(content)
        if ephemeral:
            builder = builder.ephemeral()
        return builder

    async def edit_response(self, **kwargs: Any) -> hikari.Message:
        return await self.interaction.edit_initial_response(**kwargs)

    async def defer(self, *, ephemeral: bool = False) -> None:
        flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.MessageFlag.NONE
        await self.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            flags=flags,
        )


__all__ = ["InteractionContext", "ResponseBuilder"]
