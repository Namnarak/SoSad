"""Pre-condition validators."""
from sosad.checks.base import CheckResult
from sosad.checks.builtin import (
    bot_has_permissions,
    dm_only,
    guild_only,
    has_permissions,
    has_role,
    in_guild,
    is_owner,
)
from sosad.checks.decorator import check

__all__ = [
    "CheckResult",
    "bot_has_permissions",
    "check",
    "dm_only",
    "guild_only",
    "has_permissions",
    "has_role",
    "in_guild",
    "is_owner",
]
