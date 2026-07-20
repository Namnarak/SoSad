"""Common permission presets."""

from __future__ import annotations

import hikari

ADMINISTRATOR = hikari.Permissions.ADMINISTRATOR
BAN_MEMBERS = hikari.Permissions.BAN_MEMBERS
KICK_MEMBERS = hikari.Permissions.KICK_MEMBERS
MANAGE_MESSAGES = hikari.Permissions.MANAGE_MESSAGES
MANAGE_CHANNELS = hikari.Permissions.MANAGE_CHANNELS
MANAGE_GUILD = hikari.Permissions.MANAGE_GUILD

__all__ = [
    "ADMINISTRATOR",
    "BAN_MEMBERS",
    "KICK_MEMBERS",
    "MANAGE_CHANNELS",
    "MANAGE_GUILD",
    "MANAGE_MESSAGES",
]
