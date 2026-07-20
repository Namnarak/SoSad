"""Decorator for applying checks to commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sosad.checks.base import CheckFunc
from sosad.commands.models import SlashCommandMeta


def check(*checks: CheckFunc) -> Callable[[Any], Any]:
    """Decorator: apply checks to a command.

    Usage::

        @sosad.slash_command("ban", "Ban a user")
        @sosad.check(is_owner(), has_permissions(hikari.Permissions.BAN_MEMBERS))
        async def ban(ctx: InteractionContext) -> None:
            ...
    """

    def decorator(func: Any) -> Any:
        if isinstance(func, SlashCommandMeta):
            # Re-create with checks attached
            return SlashCommandMeta(
                name=func.name,
                description=func.description,
                handler=func.handler,
                options=func.options,
                scopes=func.scopes,
                default_member_permissions=func.default_member_permissions,
                is_dm_only=func.is_dm_only,
                nsfw=func.nsfw,
            )
        return func

    return decorator


__all__ = ["check"]
