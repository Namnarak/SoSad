"""Decorator for applying checks to commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from sosad.checks.base import CheckFunc
from sosad.commands.models import SlashCommandMeta, SubCommandMeta
from sosad.commands.registration import register_command


def check(*checks: CheckFunc) -> Callable[[Any], Any]:
    """Decorator: apply checks to a command.

    Usage::

        @sosad.slash_command("ban", "Ban a user")
        @sosad.check(is_owner(), has_permissions(hikari.Permissions.BAN_MEMBERS))
        async def ban(ctx: InteractionContext) -> None:
            ...
    """

    def decorator(func: Any) -> Any:
        if isinstance(func, (SlashCommandMeta, SubCommandMeta)):
            meta = replace(func, checks=(*func.checks, *checks))
            register_command(meta)
            return meta
        existing = tuple(getattr(func, "__sosad_checks__", ()))
        func.__sosad_checks__ = (*existing, *checks)
        return func

    return decorator


__all__ = ["check"]
