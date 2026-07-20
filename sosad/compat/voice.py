"""Voice support — high-level voice API built on hikari.

Usage::

    import sosad.compat as discord

    @bot.command(name="join")
    async def join(ctx, channel: discord.VoiceChannel):
        vc = await channel.connect()
        await ctx.send(f"Joined {channel.name}")

    @bot.command(name="play")
    async def play(ctx, *, url: str):
        vc = ctx.voice_client
        if vc:
            await vc.play(url)
"""

from __future__ import annotations

from typing import Any

import hikari

__all__ = [
    "VoiceChannel",
    "VoiceClient",
    "VoiceState",
    "VoiceRegion",
]


class VoiceChannel:
    """Wrapper around hikari voice channels for easy connection."""

    def __init__(self, channel: hikari.GuildVoiceChannel) -> None:
        self._channel = channel

    @property
    def id(self) -> int:
        return self._channel.id

    @property
    def name(self) -> str:
        return self._channel.name

    @property
    def guild_id(self) -> int:
        return self._channel.guild_id

    @property
    def bitrate(self) -> int:
        return self._channel.bitrate

    @property
    def user_limit(self) -> int:
        return self._channel.user_limit

    async def connect(self) -> VoiceClient:
        """Connect to this voice channel."""
        return await VoiceClient.connect(self._channel)


class VoiceClient:
    """High-level voice connection wrapper."""

    def __init__(self, connection: hikari.VoiceConnection) -> None:
        self._connection = connection

    @staticmethod
    async def connect(
        channel: hikari.GuildVoiceChannel,
        *,
        mute: bool = False,
        deaf: bool = False,
    ) -> VoiceClient:
        """Connect to a voice channel."""
        connection = await channel.connect(mute=mute, deaf=deaf)
        return VoiceClient(connection)

    @property
    def channel_id(self) -> int | None:
        return self._connection.channel_id

    @property
    def guild_id(self) -> int:
        return self._connection.guild_id

    @property
    def is_connected(self) -> bool:
        return not self._connection.is_closed

    async def disconnect(self) -> None:
        """Disconnect from voice."""
        await self._connection.disconnect()

    async def move(self, channel: hikari.GuildVoiceChannel) -> None:
        """Move to a different voice channel."""
        await self._connection.move_to(channel)

    async def play(self, source: str | Any) -> None:
        """Play audio from a source.

        Args:
            source: URL or local path to audio file.
        """
        # In production, use a decoder like FFmpeg
        raise NotImplementedError(
            "Audio playback requires FFmpeg integration. "
            "Use hikari's voice API directly for now."
        )

    async def stop(self) -> None:
        """Stop playback."""
        await self._connection.disconnect()


# Re-export hikari voice types for convenience
VoiceState = hikari.VoiceState
VoiceRegion = hikari.VoiceRegion
