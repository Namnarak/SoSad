"""Tests for the rate limit API client."""

from __future__ import annotations

import asyncio
import time

import pytest

from sosad.api.rate_limit import RateLimitBucket, RateLimitState, parse_route
from sosad.errors import RateLimited


class TestRateLimitBucket:
    def test_create(self):
        bucket = RateLimitBucket(
            route="test",
            limit=10,
            remaining=5,
            reset_after=1.0,
            reset_at=time.time() + 1.0,
        )
        assert bucket.route == "test"
        assert bucket.limit == 10
        assert bucket.remaining == 5

    def test_frozen(self):
        bucket = RateLimitBucket(
            route="test", limit=10, remaining=5,
            reset_after=1.0, reset_at=time.time() + 1.0,
        )
        with pytest.raises(Exception):
            bucket.remaining = 0  # frozen dataclass

    def test_equality(self):
        a = RateLimitBucket(route="r", limit=1, remaining=1, reset_after=0.0, reset_at=0.0)
        b = RateLimitBucket(route="r", limit=1, remaining=1, reset_after=0.0, reset_at=0.0)
        assert a == b


class TestRateLimitState:
    def test_init(self):
        state = RateLimitState()
        assert state._buckets == {}
        assert state._global_reset == 0.0

    def test_update_from_headers(self):
        state = RateLimitState()
        bucket = state.update_from_headers("test", {
            "x-ratelimit-limit": "10",
            "x-ratelimit-remaining": "8",
            "x-ratelimit-reset-after": "2.0",
            "x-ratelimit-reset": str(time.time() + 2.0),
        })
        assert bucket is not None
        assert bucket.limit == 10
        assert bucket.remaining == 8

    def test_update_from_headers_no_headers(self):
        state = RateLimitState()
        bucket = state.update_from_headers("test", {})
        assert bucket is None

    def test_is_rate_limited_no_bucket(self):
        state = RateLimitState()
        limited, retry = state.is_rate_limited("unknown")
        assert limited is False
        assert retry == 0.0

    def test_consume(self):
        state = RateLimitState()
        state.update_from_headers("test", {
            "x-ratelimit-limit": "10",
            "x-ratelimit-remaining": "5",
            "x-ratelimit-reset-after": "10.0",
            "x-ratelimit-reset": str(time.time() + 10.0),
        })
        state.consume("test")
        bucket = state._buckets["test"]
        assert bucket.remaining == 4

    def test_consume_unknown_route(self):
        state = RateLimitState()
        state.consume("unknown")  # Should not raise

    def test_mark_global_rate_limited(self):
        state = RateLimitState()
        state.mark_global_rate_limited(5.0)
        limited, retry = state.is_rate_limited("any")
        assert limited is True
        assert 0 < retry <= 5.0

    def test_global_expires(self):
        state = RateLimitState()
        state.mark_global_rate_limited(0.01)
        time.sleep(0.02)
        limited, _ = state.is_rate_limited("any")
        assert limited is False


class TestParseRoute:
    def test_simple(self):
        result = parse_route("GET", "/api/v10/users/@me")
        assert result == "GET:api:v10:users:@me"

    def test_with_channel(self):
        result = parse_route("POST", "/api/v10/channels/123/messages")
        assert "channels" in result
        assert "123" in result

    def test_with_guild(self):
        result = parse_route("GET", "/api/v10/guilds/456/members")
        assert "guilds" in result
        assert "456" in result

    def test_with_webhook(self):
        result = parse_route("POST", "/api/v10/webhooks/789/abc")
        assert "webhooks" in result
        assert "789" in result

    def test_method_upper(self):
        result = parse_route("post", "/api/v10/test")
        assert result.startswith("POST")

    def test_empty_path(self):
        result = parse_route("GET", "")
        assert result == "GET"


class TestRateLimitedError:
    def test_exception(self):
        exc = RateLimited("Test limit", retry_after=5.0)
        assert str(exc) == "Test limit"
        assert exc.retry_after == 5.0
        assert isinstance(exc, Exception)

    def test_default_retry(self):
        exc = RateLimited("Limit")
        assert exc.retry_after == 0.0

    def test_subclass(self):
        from sosad.errors import SoSadError
        exc = RateLimited("Limit")
        assert isinstance(exc, SoSadError)
