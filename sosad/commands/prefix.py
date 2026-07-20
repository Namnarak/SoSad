"""Prefix command system — message-based commands like !ping."""

from __future__ import annotations

import shlex
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import hikari

if TYPE_CHECKING:
    from sosad.core.base_client import BaseClient


@dataclass
class PrefixContext:
    """Context for a prefix command (message-based)."""

    message: hikari.Message
    client: BaseClient
    command_name: str
    args: list[str] = field(default_factory=list)

    @property
    def author(self) -> hikari.User:
        return self.message.author

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        return self.message.guild_id

    @property
    def channel_id(self) -> hikari.Snowflake:
        return self.message.channel_id

    @property
    def content(self) -> str:
        return self.message.content

    async def send(
        self,
        content: str | None = None,
        *,
        embed: hikari.Embed | None = None,
        embeds: list[hikari.Embed] | None = None,
        **kwargs: Any,
    ) -> hikari.Message:
        if embed is not None:
            return await self.message.respond(content, embed=embed, **kwargs)
        return await self.message.respond(content, embeds=embeds, **kwargs)

    async def reply(
        self,
        content: str | None = None,
        **kwargs: Any,
    ) -> hikari.Message:
        return await self.send(content, **kwargs)


PrefixHandler = Callable[[PrefixContext], Any]


class PrefixRegistry:
    """Registry for prefix commands (!ping, !help, etc.)."""

    def __init__(self) -> None:
        self._commands: dict[str, PrefixHandler] = {}

    def add(self, name: str, handler: PrefixHandler) -> None:
        self._commands[name] = handler

    def resolve(self, name: str) -> PrefixHandler | None:
        return self._commands.get(name)

    def remove(self, name: str) -> bool:
        return self._commands.pop(name, None) is not None

    @property
    def command_names(self) -> list[str]:
        return list(self._commands.keys())


_global_prefix_registry = PrefixRegistry()


def get_prefix_registry() -> PrefixRegistry:
    return _global_prefix_registry


def prefix_command(name: str | None = None) -> Callable[[PrefixHandler], PrefixHandler]:
    """Decorator to register a prefix command (!ping).

    Usage::

        from sosad.commands.prefix import prefix_command

        @prefix_command(name="ping")
        async def ping(ctx: PrefixContext) -> None:
            await ctx.send("Pong!")
    """
    def decorator(func: PrefixHandler) -> PrefixHandler:
        cmd_name = name or func.__name__
        _global_prefix_registry.add(cmd_name, func)
        return func
    return decorator


async def handle_prefix_message(
    message: hikari.Message,
    client: BaseClient,
    prefix: str = "!",
    registry: PrefixRegistry | None = None,
) -> bool:
    """Handle a potential prefix command message.

    Returns True if the message was handled as a prefix command.
    """
    if message.author.is_bot or message.author.is_system:
        return False

    content = message.content
    if not content or not content.startswith(prefix):
        return False

    reg = registry or _global_prefix_registry

    parts = shlex.split(content[len(prefix):])
    if not parts:
        return False

    cmd_name = parts[0].lower()
    cmd_args = parts[1:]

    handler = reg.resolve(cmd_name)
    if handler is None:
        return False

    ctx = PrefixContext(
        message=message,
        client=client,
        command_name=cmd_name,
        args=cmd_args,
    )

    try:
        await handler(ctx)
    except Exception:
        import logging
        logger = logging.getLogger("sosad.prefix")
        logger.exception("Error in prefix command: %s", cmd_name)

    return True


__all__ = [
    "PrefixContext",
    "PrefixHandler",
    "PrefixRegistry",
    "get_prefix_registry",
    "handle_prefix_message",
    "prefix_command",
]
