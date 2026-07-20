"""Decorator for permission checking."""

from __future__ import annotations

import hikari

from sosad.checks.base import CheckFunc, CheckResult
from sosad.permissions.resolver import PermissionResolver


def requires_permissions(*perms: hikari.Permissions) -> CheckFunc:
    """Check that the author has specific permissions.

    Usage::

        @sosad.slash_command("purge", "Delete messages")
        @sosad.requires_permissions(hikari.Permissions.MANAGE_MESSAGES)
        async def purge(ctx: InteractionContext) -> None:
            ...
    """

    async def _check(ctx: object) -> CheckResult:
        from sosad.context.context import InteractionContext

        if not isinstance(ctx, InteractionContext):
            return CheckResult.fail("Invalid context.")
        if ctx.guild_id is None:
            return CheckResult.fail("This command can only be used in a guild.")
        member_perms = PermissionResolver.resolve_member_permissions(ctx.interaction)
        required = perms[0]
        if PermissionResolver.has_permission(member_perms, required):
            return CheckResult.ok()
        return CheckResult.fail("You don't have the required permissions.")

    return _check


__all__ = ["requires_permissions"]
