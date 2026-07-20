"""Permission bitfield resolution."""

from __future__ import annotations

import hikari


class PermissionResolver:
    """Resolves permissions from interaction context."""

    @staticmethod
    def resolve_member_permissions(
        interaction: hikari.CommandInteraction,
    ) -> hikari.Permissions:
        """Get the member's effective permissions in the channel."""
        member = interaction.get_member()
        if member is None:
            return hikari.Permissions.NONE
        return member.permissions

    @staticmethod
    def has_permission(
        member_permissions: hikari.Permissions,
        required: hikari.Permissions,
    ) -> bool:
        """Check if member has the required permissions."""
        return (member_permissions & required) == required


__all__ = ["PermissionResolver"]
