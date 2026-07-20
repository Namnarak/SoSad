"""discord.py-compatible app_commands (slash command decorators).

Usage::

    from discord.app_commands import command, describe, choices, Choice

    @bot.tree.command(name="ping", description="Ping!")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import sosad


class Choice:
    """A choice option for a slash command parameter.

    Usage::

        @app_commands.choices(color=[
            Choice(name="Red", value="red"),
            Choice(name="Blue", value="blue"),
        ])
        async def pick(ctx, color: str): ...
    """

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value}


def command(
    name: str,
    description: str | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register an app command (slash command).

    Usage::

        @app_commands.command(name="ping", description="Ping!")
        async def ping(interaction, ctx): ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cmd_desc = description or func.__doc__ or name

        @sosad.slash_command(name, cmd_desc, **kwargs)
        async def wrapper(ctx: Any) -> None:
            await func(ctx.interaction, ctx)

        return func
    return decorator


def describe(
    **kwargs: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Add descriptions to command parameters.

    Usage::

        @app_commands.describe(
            user="The user to greet",
            message="The message to send",
        )
        async def greet(ctx, user: str, message: str): ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._sosad_descriptions = kwargs
        return func
    return decorator


def choices(
    **kwargs: list[Choice],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Add choices to command parameters.

    Usage::

        @app_commands.choices(color=[
            Choice(name="Red", value="red"),
            Choice(name="Blue", value="blue"),
        ])
        async def pick(ctx, color: str): ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._sosad_choices = {
            name: [c.to_dict() for c in choices_list]
            for name, choices_list in kwargs.items()
        }
        return func
    return decorator


def rename(
    **kwargs: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Rename command parameters.

    Usage::

        @app_commands.rename(user="member")
        async def greet(ctx, user: str): ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._sosad_renames = kwargs
        return func
    return decorator


__all__ = ["Choice", "choices", "command", "describe", "rename"]
