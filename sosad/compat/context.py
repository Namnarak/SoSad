"""discord.py-compatible interaction and prefix contexts."""

from __future__ import annotations

from typing import Any

import hikari

from sosad.commands.prefix import PrefixContext
from sosad.context.context import InteractionContext


class Context:
    """A small context facade shared by slash, hybrid, and prefix commands."""

    @classmethod
    def __class_getitem__(cls, item: Any) -> type[Context]:
        """Accept discord.py's ``Context[BotT]`` annotation form."""
        del item
        return cls

    def __init__(self, interaction_ctx: Any, *, bot: Any = None) -> None:
        self._ctx = interaction_ctx
        self._bot = bot

    @classmethod
    def from_sad(cls, ctx: InteractionContext, *, bot: Any = None) -> Context:
        return cls(ctx, bot=bot)

    @classmethod
    def from_prefix(cls, ctx: PrefixContext, *, bot: Any = None) -> Context:
        return cls(ctx, bot=bot)

    @property
    def interaction(self) -> Any:
        from sosad.compat.interaction import wrap_interaction

        return wrap_interaction(getattr(self._ctx, "interaction", None))

    @property
    def author(self) -> Any:
        return self._ctx.author

    @property
    def guild(self) -> Any:
        guild_id = getattr(self._ctx, "guild_id", None)
        if guild_id is None:
            return None
        native_client = getattr(self._ctx, "client", None)
        try:
            gateway = native_client.bot
            if hasattr(gateway, "cache"):
                cached = gateway.cache.get_guild(guild_id)
                if cached is not None:
                    return cached
        except (AttributeError, RuntimeError):
            pass
        return guild_id

    @property
    def guild_id(self) -> int | None:
        guild_id = getattr(self._ctx, "guild_id", None)
        return int(guild_id) if guild_id else None

    @property
    def channel(self) -> Any:
        channel_id = getattr(self._ctx, "channel_id", None)
        native_client = getattr(self._ctx, "client", None)
        try:
            gateway = native_client.bot
            if hasattr(gateway, "cache") and channel_id is not None:
                cached = gateway.cache.get_guild_channel(channel_id)
                if cached is not None:
                    return cached
        except (AttributeError, RuntimeError):
            pass
        return channel_id

    @property
    def channel_id(self) -> int:
        return int(self._ctx.channel_id)

    @property
    def message(self) -> Any:
        return getattr(self._ctx, "message", None)

    @property
    def bot(self) -> Any:
        return self._bot or getattr(self._ctx, "client", None)

    @property
    def client(self) -> Any:
        return self.bot

    @property
    def me(self) -> Any:
        return getattr(self.bot, "user", None) or self.author

    @property
    def command(self) -> Any:
        return getattr(self, "_command", None)

    @property
    def invoked_subcommand(self) -> Any:
        return getattr(self, "_invoked_subcommand", None)

    async def send(
        self,
        content: str | None = None,
        *,
        embed: hikari.Embed | None = None,
        embeds: list[hikari.Embed] | None = None,
        ephemeral: bool = False,
        tts: bool = False,
        file: hikari.File | None = None,
        files: list[hikari.File] | None = None,
        view: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Send through either an interaction response or a message context."""
        del tts
        if isinstance(self._ctx, PrefixContext):
            if view is not None:
                kwargs["components"] = view
            if file is not None:
                kwargs["file"] = file
            if files is not None:
                kwargs["files"] = files
            return await self._ctx.send(content, embed=embed, embeds=embeds, **kwargs)

        builder = self._ctx.respond(content)
        if ephemeral:
            builder = builder.ephemeral()
        if embed is not None:
            builder = builder.embed(embed)
        if embeds:
            builder = builder.embeds(*embeds)
        if file is not None:
            builder = builder.file(file)
        if files:
            builder = builder.files(*files)
        if view is not None:
            builder = builder.components(view)
        return await builder.send()

    async def respond(self, content: str | None = None, **kwargs: Any) -> Any:
        return await self.send(content, **kwargs)

    async def defer(self, *, ephemeral: bool = False) -> None:
        if isinstance(self._ctx, PrefixContext):
            return None
        await self._ctx.defer(ephemeral=ephemeral)

    async def edit(self, content: str | None = None, **kwargs: Any) -> Any:
        return await self._ctx.edit_response(content=content, **kwargs)

    async def delete(self) -> None:
        interaction = self.interaction
        if interaction is not None:
            from contextlib import suppress

            with suppress(Exception):
                await interaction.delete_initial_response()

    async def reply(self, content: str | None = None, **kwargs: Any) -> Any:
        return await self.send(content, **kwargs)


__all__ = ["Context"]
