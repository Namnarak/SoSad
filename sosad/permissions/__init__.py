"""Permission checking integration."""
from sosad.permissions.builtin import ADMINISTRATOR, BAN_MEMBERS, MANAGE_MESSAGES
from sosad.permissions.decorator import requires_permissions
from sosad.permissions.resolver import PermissionResolver

__all__ = [
    "ADMINISTRATOR",
    "BAN_MEMBERS",
    "MANAGE_MESSAGES",
    "PermissionResolver",
    "requires_permissions",
]
