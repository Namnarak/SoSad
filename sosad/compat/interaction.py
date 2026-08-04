"""Adapters for discord.py's ``Interaction.response`` API."""

from __future__ import annotations

from typing import Any

import hikari

from sosad.context.context import ResponseBuilder


class InteractionResponse:
    def __init__(self, interaction: Interaction) -> None:
        self._interaction = interaction
        self._done = False

    def is_done(self) -> bool:
        return self._done

    async def send_message(self, content: str | None = None, **kwargs: Any) -> Any:
        self._done = True
        return await self._interaction._build_response(content, kwargs).send()

    async def edit_message(self, content: str | None = None, **kwargs: Any) -> Any:
        self._done = True
        return await self._interaction.edit_original_response(content=content, **kwargs)

    async def send_modal(self, modal: Any) -> Any:
        self._done = True
        return await ResponseBuilder(_interaction=self._interaction._raw).modal(modal).send()

    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> Any:
        del thinking
        self._done = True
        return await self._interaction._raw.create_initial_response(
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            flags=hikari.MessageFlag.EPHEMERAL if ephemeral else hikari.MessageFlag.NONE,
        )


class InteractionFollowup:
    def __init__(self, interaction: Interaction) -> None:
        self._interaction = interaction

    async def send(self, content: str | None = None, **kwargs: Any) -> Any:
        rest = getattr(getattr(self._interaction._raw, "app", None), "rest", None)
        if rest is None:
            return await self._interaction._build_response(content, kwargs).send()
        payload = dict(kwargs)
        payload.pop("wait", None)
        payload.pop("ephemeral", None)
        return await rest.execute_webhook(
            self._interaction._raw.application_id,
            self._interaction._raw.token,
            content=content,
            **payload,
        )


class Interaction:
    """A delegating wrapper that adds discord.py response helpers."""

    @classmethod
    def __class_getitem__(cls, item: Any) -> type[Interaction]:
        """Accept discord.py's ``Interaction[ClientT]`` annotation form."""
        del item
        return cls

    def __init__(self, interaction: hikari.PartialInteraction) -> None:
        self._raw = interaction
        self.response = InteractionResponse(self)
        self.followup = InteractionFollowup(self)

    def _build_response(self, content: str | None, kwargs: dict[str, Any]) -> ResponseBuilder:
        builder = ResponseBuilder(_interaction=self._raw)
        if content is not None:
            builder = builder.content(content)
        if kwargs.get("ephemeral"):
            builder = builder.ephemeral()
        if kwargs.get("embed") is not None:
            builder = builder.embed(kwargs["embed"])
        if kwargs.get("embeds"):
            builder = builder.embeds(*kwargs["embeds"])
        if kwargs.get("file") is not None:
            builder = builder.file(kwargs["file"])
        if kwargs.get("files"):
            builder = builder.files(*kwargs["files"])
        if kwargs.get("view") is not None:
            builder = builder.components(kwargs["view"])
        return builder

    async def edit_original_response(self, content: str | None = None, **kwargs: Any) -> Any:
        if content is not None:
            kwargs["content"] = content
        if "embed" in kwargs:
            kwargs["embeds"] = [kwargs.pop("embed")]
        view = kwargs.pop("view", None)
        if view is not None:
            kwargs["components"] = view
        return await self._raw.edit_initial_response(**kwargs)

    async def delete_original_response(self) -> Any:
        return await self._raw.delete_initial_response()

    async def original_response(self) -> Any:
        return await self._raw.fetch_initial_response()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)


def wrap_interaction(interaction: Any) -> Any:
    if isinstance(interaction, hikari.PartialInteraction):
        return Interaction(interaction)
    return interaction


__all__ = ["Interaction", "InteractionFollowup", "InteractionResponse", "wrap_interaction"]
