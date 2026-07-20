"""Type definitions for Discord REST API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HTTPMethod(StrEnum):
    """HTTP methods used by Discord API."""

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"
    PUT = "PUT"


@dataclass(frozen=True, slots=True)
class APIError:
    """Discord API error response."""

    code: int
    message: str
    errors: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"Discord API Error {self.code}: {self.message}"


@dataclass(frozen=True, slots=True)
class RESTResponse:
    """Wrapper for a REST API response."""

    status: int
    headers: dict[str, str]
    data: Any = None
    error: APIError | None = None

    @property
    def ok(self) -> bool:
        """Check if the response indicates success (2xx)."""
        return 200 <= self.status < 300

    @property
    def rate_limited(self) -> bool:
        """Check if the response is a rate limit (429)."""
        return self.status == 429


@dataclass(frozen=True, slots=True)
class MessageData:
    """Discord message object."""

    id: str
    channel_id: str
    author: dict[str, Any]
    content: str
    timestamp: str
    edited_timestamp: str | None = None
    tts: bool = False
    mention_everyone: bool = False
    mentions: list[dict[str, Any]] = field(default_factory=list)
    embeds: list[dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    components: list[dict[str, Any]] = field(default_factory=list)
    flags: int = 0


@dataclass(frozen=True, slots=True)
class ChannelData:
    """Discord channel object."""

    id: str
    type: int
    guild_id: str | None = None
    name: str | None = None
    topic: str | None = None
    nsfw: bool = False
    position: int = 0
    parent_id: str | None = None
    rate_limit_per_user: int | None = None


@dataclass(frozen=True, slots=True)
class GuildData:
    """Discord guild object."""

    id: str
    name: str
    owner: bool = False
    owner_id: str = ""
    permissions: int = 0
    region: str = ""
    afk_channel_id: str | None = None
    afk_timeout: int = 0
    icon: str | None = None
    member_count: int = 0
    large: bool = False


@dataclass(frozen=True, slots=True)
class WebhookData:
    """Discord webhook object."""

    id: str
    type: int
    guild_id: str | None = None
    channel_id: str | None = None
    user: dict[str, Any] | None = None
    name: str | None = None
    avatar: str | None = None
    token: str | None = None


@dataclass(frozen=True, slots=True)
class ApplicationCommandData:
    """Discord application command object."""

    id: str
    application_id: str
    name: str
    description: str
    type: int = 1
    guild_id: str | None = None
    options: list[dict[str, Any]] = field(default_factory=list)
    default_member_permissions: str | None = None
    dm_permission: bool = True
    nsfw: bool = False


@dataclass(frozen=True, slots=True)
class InteractionResponseData:
    """Data for responding to an interaction."""

    type: int
    data: dict[str, Any] | None = None


__all__ = [
    "APIError",
    "ApplicationCommandData",
    "ChannelData",
    "GuildData",
    "HTTPMethod",
    "InteractionResponseData",
    "MessageData",
    "RESTResponse",
    "WebhookData",
]
