"""Rate limit tracking and handling for Discord REST API."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger("sosad.api.rate_limit")


@dataclass(frozen=True, slots=True)
class RateLimitBucket:
    """A single rate limit bucket."""

    route: str
    limit: int
    remaining: int
    reset_after: float
    reset_at: float


@dataclass
class RateLimitState:
    """Tracks rate limit state for all buckets."""

    _buckets: dict[str, RateLimitBucket] = field(default_factory=dict)
    _global_reset: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def update_from_headers(
        self,
        route: str,
        headers: dict[str, str],
    ) -> RateLimitBucket | None:
        """Parse rate limit headers and update state.

        Headers:
            X-RateLimit-Limit
            X-RateLimit-Remaining
            X-RateLimit-Reset-After (seconds)
            X-RateLimit-Reset (unix timestamp)
            X-RateLimit-Bucket (route bucket hash)
        """
        limit = headers.get("x-ratelimit-limit")
        remaining = headers.get("x-ratelimit-remaining")
        reset_after = headers.get("x-ratelimit-reset-after")
        reset_at = headers.get("x-ratelimit-reset")

        if limit is None or remaining is None:
            return None

        bucket = RateLimitBucket(
            route=route,
            limit=int(limit),
            remaining=int(remaining),
            reset_after=float(reset_after or 0),
            reset_at=float(reset_at or 0),
        )
        self._buckets[route] = bucket
        return bucket

    def is_rate_limited(self, route: str) -> tuple[bool, float]:
        """Check if a route is currently rate limited.

        Returns (is_limited, retry_after_seconds).
        """
        # Check global rate limit
        now = time.monotonic()
        if self._global_reset > now:
            return True, self._global_reset - now

        # Check route-specific rate limit
        bucket = self._buckets.get(route)
        if bucket is None:
            return False, 0.0

        if bucket.remaining <= 0:
            retry_after = max(bucket.reset_at - time.time(), 0)
            return True, retry_after

        return False, 0.0

    def mark_global_rate_limited(self, retry_after: float) -> None:
        """Mark the entire API as rate limited."""
        self._global_reset = time.monotonic() + retry_after
        logger.warning("Global rate limit hit. Retry after %.2fs", retry_after)

    def consume(self, route: str) -> None:
        """Consume one request from the bucket."""
        bucket = self._buckets.get(route)
        if bucket is not None:
            self._buckets[route] = RateLimitBucket(
                route=bucket.route,
                limit=bucket.limit,
                remaining=bucket.remaining - 1,
                reset_after=bucket.reset_after,
                reset_at=bucket.reset_at,
            )


def parse_route(method: str, path: str) -> str:
    """Parse a Discord API route into a rate limit bucket key.

    Discord groups rate limits by major parameters (guild_id, channel_id, webhook_id).
    These are extracted from the path and used as part of the route key.
    """
    parts = path.strip("/").split("/")
    key_parts: list[str] = [method.upper()]

    i = 0
    while i < len(parts):
        part = parts[i]
        # Check for major parameter patterns
        if part in ("channels", "guilds", "webhooks") and i + 1 < len(parts):
            key_parts.append(part)
            key_parts.append(parts[i + 1])  # The ID
            i += 2
        else:
            key_parts.append(part)
            i += 1

    return ":".join(key_parts)


__all__ = [
    "RateLimitBucket",
    "RateLimitState",
    "parse_route",
]
