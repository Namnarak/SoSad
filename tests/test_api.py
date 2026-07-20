"""Tests for the REST API client."""

from sosad.api.rate_limit import RateLimitState, parse_route
from sosad.api.types import APIError, HTTPMethod, RESTResponse

# ── Rate Limit Tests ──

def test_parse_route_basic():
    route = parse_route("GET", "/channels/123456/messages")
    assert route == "GET:channels:123456:messages"


def test_parse_route_guild():
    route = parse_route("GET", "/guilds/789012/channels")
    assert route == "GET:guilds:789012:channels"


def test_parse_route_webhook():
    route = parse_route("POST", "/webhooks/111/222/messages")
    assert route == "POST:webhooks:111:222:messages"


def test_parse_route_no_major():
    route = parse_route("GET", "/gateway/bot")
    assert route == "GET:gateway:bot"


def test_rate_limit_state_update():
    state = RateLimitState()
    headers = {
        "x-ratelimit-limit": "5",
        "x-ratelimit-remaining": "4",
        "x-ratelimit-reset-after": "1.0",
        "x-ratelimit-reset": "1234567890.0",
    }
    bucket = state.update_from_headers("GET:channels:123:messages", headers)
    assert bucket is not None
    assert bucket.limit == 5
    assert bucket.remaining == 4


def test_rate_limit_not_limited():
    state = RateLimitState()
    headers = {
        "x-ratelimit-limit": "5",
        "x-ratelimit-remaining": "3",
        "x-ratelimit-reset-after": "1.0",
        "x-ratelimit-reset": "9999999999.0",
    }
    state.update_from_headers("test", headers)
    is_limited, _ = state.is_rate_limited("test")
    assert is_limited is False


def test_rate_limit_exhausted():
    state = RateLimitState()
    headers = {
        "x-ratelimit-limit": "5",
        "x-ratelimit-remaining": "0",
        "x-ratelimit-reset-after": "2.0",
        "x-ratelimit-reset": "9999999999.0",
    }
    state.update_from_headers("test", headers)
    is_limited, retry_after = state.is_rate_limited("test")
    assert is_limited is True
    assert retry_after > 0


def test_rate_limit_consume():
    state = RateLimitState()
    headers = {
        "x-ratelimit-limit": "2",
        "x-ratelimit-remaining": "2",
        "x-ratelimit-reset-after": "1.0",
        "x-ratelimit-reset": "9999999999.0",
    }
    state.update_from_headers("test", headers)
    state.consume("test")
    is_limited, _ = state.is_rate_limited("test")
    assert is_limited is False
    state.consume("test")
    is_limited, _ = state.is_rate_limited("test")
    assert is_limited is True


def test_global_rate_limit():
    state = RateLimitState()
    state.mark_global_rate_limited(1.0)
    is_limited, retry_after = state.is_rate_limited("anything")
    assert is_limited is True
    assert retry_after > 0


# ── RESTResponse Tests ──

def test_rest_response_ok():
    resp = RESTResponse(status=200, headers={}, data={"id": "123"})
    assert resp.ok is True
    assert resp.rate_limited is False


def test_rest_response_error():
    resp = RESTResponse(
        status=400,
        headers={},
        error=APIError(code=50035, message="Invalid Form Body"),
    )
    assert resp.ok is False
    assert resp.error is not None
    assert resp.error.code == 50035


def test_rest_response_rate_limited():
    resp = RESTResponse(status=429, headers={})
    assert resp.rate_limited is True
    assert resp.ok is False


def test_api_error_str():
    err = APIError(code=10013, message="Unknown User")
    assert "10013" in str(err)
    assert "Unknown User" in str(err)


# ── HTTPMethod Tests ──

def test_http_method_values():
    assert HTTPMethod.GET.value == "GET"
    assert HTTPMethod.POST.value == "POST"
    assert HTTPMethod.PATCH.value == "PATCH"
    assert HTTPMethod.DELETE.value == "DELETE"
    assert HTTPMethod.PUT.value == "PUT"
