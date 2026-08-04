"""discord.py-shaped exception namespace."""

from __future__ import annotations

from sosad.compat.types import DiscordException, Forbidden, HTTPException, NotFound


class ClientException(DiscordException):
    """Base exception for client-side compatibility errors."""


class InvalidArgument(ClientException):
    """Raised when a compatibility API receives an invalid argument."""


__all__ = [
    "ClientException",
    "DiscordException",
    "Forbidden",
    "HTTPException",
    "InvalidArgument",
    "NotFound",
]
