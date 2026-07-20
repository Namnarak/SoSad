"""Immutable interaction context and response builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

import hikari

if TYPE_CHECKING:
    from sosad.core.app import App
    from sosad.core.client import Client


_MISSING = object()


@dataclass(frozen=True, slots=True)
class ResponseBuilder:
    """Immutable builder for interaction responses. Each method returns a new builder."""

    _interaction: hikari.CommandInteraction
    _response_type: hikari.ResponseType = field(default=hikari.ResponseType.MESSAGE_CREATE)
    _content: str | None = None
    _embeds: tuple[hikari.Embed, ...] = ()
    _files: tuple[hikari.File, ...] = ()
    _flags: hikari.MessageFlag = field(default=hikari.MessageFlag.NONE)
    _components: tuple[Any, ...] = ()

    def content(self, text: str) -> Self:
        """Set the message content."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=text,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
        )

    def embed(self, embed: hikari.Embed) -> Self:
        """Add a single embed."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=(*self._embeds, embed),
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
        )

    def embeds(self, *embeds: hikari.Embed) -> Self:
        """Add multiple embeds."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=(*self._embeds, *embeds),
            _files=self._files,
            _flags=self._flags,
            _components=self._components,
        )

    def file(self, file: hikari.File) -> Self:
        """Add a file attachment."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=(*self._files, file),
            _flags=self._flags,
            _components=self._components,
        )

    def files(self, *files: hikari.File) -> Self:
        """Add multiple file attachments."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=(*self._files, *files),
            _flags=self._flags,
            _components=self._components,
        )

    def ephemeral(self) -> Self:
        """Make the response ephemeral (only visible to the invoker)."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags | hikari.MessageFlag.EPHEMERAL,
            _components=self._components,
        )

    def flag(self, flag: hikari.MessageFlag) -> Self:
        """Add a message flag."""
        return self.__class__(
            _interaction=self._interaction,
            _response_type=self._response_type,
            _content=self._content,
            _embeds=self._embeds,
            _files=self._files,
            _flags=self._flags | flag,
            _components=self._components,
        )

    async def send(self) -> hikari.MessageResponse[hikari.CommandInteraction]:
        """Execute the response."""
        builder = self._interaction.build_response(self._response_type)
        if self._content is not None:
            builder = builder.set_content(self._content)
        for embed in self._embeds:
            builder = builder.add_embed(embed)
        for f in self._files:
            builder = builder.add_file(f)
        if self._flags is not hikari.MessageFlag.NONE:
            builder = builder.set_flags(self._flags)
        return await builder.create_initial_response()

    async def defer(self, *, ephemeral: bool = False) -> None:
        """Defer the interaction response."""
        flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.MessageFlag.NONE
        await self._interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            flags=flags,
        )


@dataclass(frozen=True, slots=True)
class InteractionContext:
    """Immutable snapshot of an interaction. Created once per request."""

    interaction: hikari.CommandInteraction
    client: Client
    app: App

    @property
    def author(self) -> hikari.User:
        """The user who invoked the command."""
        return self.interaction.user

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        """Guild ID if in a guild, else None."""
        return self.interaction.guild_id

    @property
    def channel_id(self) -> hikari.Snowflake:
        """The channel ID where the command was invoked."""
        return self.interaction.channel_id

    @property
    def options(self) -> dict[str, hikari.CommandInteractionOption]:
        """All options as a name-to-option dict."""
        return {opt.name: opt for opt in (self.interaction.options or ())}

    def get_option(self, name: str, default: Any = _MISSING) -> Any:
        """Get an option value by name. Returns default if not found."""
        opts = self.options
        if name not in opts:
            if default is _MISSING:
                raise KeyError(f"Option '{name}' not found")
            return default
        return opts[name].value

    def get_str(self, name: str) -> str:
        """Get a string option value."""
        value = self.get_option(name)
        if not isinstance(value, str):
            raise TypeError(f"Option '{name}' is not a string, got {type(value)}")
        return value

    def get_int(self, name: str) -> int:
        """Get an integer option value."""
        value = self.get_option(name)
        if not isinstance(value, int):
            raise TypeError(f"Option '{name}' is not an int, got {type(value)}")
        return value

    def get_user(self, name: str) -> hikari.User:
        """Get a user option value."""
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
            raise ValueError(f"User {user_id} not found in resolved data")
        return user

    def respond(self) -> ResponseBuilder:
        """Create a response builder for this interaction."""
        return ResponseBuilder(interaction=self.interaction)

    async def edit_response(self, **kwargs: Any) -> hikari.Message:
        """Edit the initial response."""
        return await self.interaction.edit_initial_response(**kwargs)

    async def defer(self, *, ephemeral: bool = False) -> None:
        """Defer the interaction response."""
        flags = hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.MessageFlag.NONE
        await self.interaction.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            flags=flags,
        )


__all__ = ["InteractionContext", "ResponseBuilder"]
