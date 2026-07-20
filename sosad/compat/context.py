"""discord.py-compatible Context class."""

from __future__ import annotations

from typing import Any

import hikari

from sosad.context.context import InteractionContext


class Context:
    """discord.py-compatible Context that wraps SoSad InteractionContext.

    Usage::

        # Works like discord.py's ctx:
        await ctx.send("Hello!")
        await ctx.send("Ephemeral", ephemeral=True)
        await ctx.send(embed=my_embed)
    """

    def __init__(self, interaction_ctx: InteractionContext) -> None:
        self._ctx = interaction_ctx

    @classmethod
    def from_sad(cls, ctx: InteractionContext) -> Context:
        return cls(ctx)

    @property
    def interaction(self) -> hikari.CommandInteraction:
        return self._ctx.interaction

    @property
    def author(self) -> hikari.User:
        return self._ctx.author

    @property
    def guild(self) -> Any:
        return self._ctx.guild_id

    @property
    def channel(self) -> hikari.Snowflake:
        return self._ctx.channel_id

    @property
    def message(self) -> Any:
        return None

    @property
    def bot(self) -> Any:
        return self._ctx.client

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
        **kwargs: Any,
    ) -> Any:
        """Send a response (compatible with discord.py ctx.send)."""
        builder = self._ctx.respond(content)
        if ephemeral:
            builder = builder.ephemeral()
        if embed:
            builder = builder.embed(embed)
        if embeds:
            builder = builder.embeds(*embeds)
        if file:
            builder = builder.file(file)
        if files:
            builder = builder.files(*files)
        return await builder.send()

    async def respond(self, content: str | None = None, **kwargs: Any) -> Any:
        """Respond to the interaction."""
        return await self.send(content, **kwargs)

    async def defer(self, *, ephemeral: bool = False) -> None:
        """Defer the interaction."""
        await self._ctx.defer(ephemeral=ephemeral)


__all__ = ["Context"]
