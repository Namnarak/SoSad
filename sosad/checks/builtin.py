"""Built-in check functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import hikari

from sosad.checks.base import CheckResult

if TYPE_CHECKING:
    from sosad.context.context import InteractionContext


def is_owner(*user_ids: hikari.Snowflake) -> CheckFunc:
    """Check that the author is one of the specified owner IDs.

    If no IDs are provided, checks against the bot application owner.
    """

    async def _check(ctx: InteractionContext) -> CheckResult:
        if user_ids:
            if ctx.author.id in user_ids:
                return CheckResult.ok()
            return CheckResult.fail("You are not the bot owner.")
        return CheckResult.fail("No owner IDs configured.")

    return _check


def has_permissions(*perms: hikari.Permissions) -> CheckFunc:
    """Check that the author has the specified permissions."""

    async def _check(ctx: InteractionContext) -> CheckResult:
        if ctx.guild_id is None:
            return CheckResult.fail("This command can only be used in a guild.")
        member = ctx.interaction.member
        if member is None:
            return CheckResult.fail("Could not resolve member.")
        if member.permissions & perms[0] == perms[0]:
            return CheckResult.ok()
        return CheckResult.fail("You don't have the required permissions.")

    return _check


def has_role(*role_ids: hikari.Snowflake) -> CheckFunc:
    """Check that the author has one of the specified roles."""

    async def _check(ctx: InteractionContext) -> CheckResult:
        if ctx.guild_id is None:
            return CheckResult.fail("This command can only be used in a guild.")
        member = ctx.interaction.member
        if member is None:
            return CheckResult.fail("Could not resolve member.")
        member_roles = set(member.role_ids)
        if member_roles & set(role_ids):
            return CheckResult.ok()
        return CheckResult.fail("You don't have the required role.")

    return _check


def in_guild() -> CheckFunc:
    """Check that the command is used in a guild."""

    async def _check(ctx: InteractionContext) -> CheckResult:
        if ctx.guild_id is not None:
            return CheckResult.ok()
        return CheckResult.fail("This command can only be used in a guild.")

    return _check


def dm_only() -> CheckFunc:
    """Check that the command is used in DMs."""

    async def _check(ctx: InteractionContext) -> CheckResult:
        if ctx.guild_id is None:
            return CheckResult.ok()
        return CheckResult.fail("This command can only be used in DMs.")

    return _check


def guild_only() -> CheckFunc:
    """Check that the command is used in a guild (alias for in_guild)."""
    return in_guild()


def bot_has_permissions(*perms: hikari.Permissions) -> CheckFunc:
    """Check that the bot has the specified permissions."""

    async def _check(ctx: InteractionContext) -> CheckResult:
        if ctx.guild_id is None:
            return CheckResult.fail("This command can only be used in a guild.")
        try:
            bot_user = ctx.client.bot.get_me()
            if bot_user is None:
                return CheckResult.fail("Could not resolve bot user.")
            me = await ctx.client.bot.rest.fetch_member(ctx.guild_id, bot_user.id)
        except Exception:
            return CheckResult.fail("Could not resolve bot member.")
        if me.permissions & perms[0] == perms[0]:
            return CheckResult.ok()
        return CheckResult.fail("I don't have the required permissions.")

    return _check


# Re-export for type checking
from sosad.checks.base import CheckFunc  # noqa: E402

__all__ = [
    "CheckFunc",
    "bot_has_permissions",
    "dm_only",
    "guild_only",
    "has_permissions",
    "has_role",
    "in_guild",
    "is_owner",
]
