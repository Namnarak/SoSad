"""REST API client for Discord."""

from sosad.api.client import RESTClient
from sosad.api.rate_limit import RateLimitState, parse_route
from sosad.api.types import (
    APIError,
    ApplicationCommandData,
    ChannelData,
    GuildData,
    HTTPMethod,
    InteractionResponseData,
    MessageData,
    RESTResponse,
    WebhookData,
)

__all__ = [
    "APIError",
    "ApplicationCommandData",
    "ChannelData",
    "GuildData",
    "HTTPMethod",
    "InteractionResponseData",
    "MessageData",
    "RESTClient",
    "RESTResponse",
    "RateLimitState",
    "WebhookData",
    "parse_route",
]
