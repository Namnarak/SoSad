"""Tests for checks and cooldowns."""

import pytest

from sosad.checks.base import CheckResult
from sosad.checks.decorator import check
from sosad.commands.executor import execute_command
from sosad.commands.models import SlashCommandMeta
from sosad.cooldowns.buckets import BucketScope, CooldownConfig
from sosad.cooldowns.storage import InMemoryCooldownStorage
from sosad.di.scopes import ScopeManager
from sosad.errors import CheckFailed, RateLimited


def test_check_result_ok():
    result = CheckResult.ok()
    assert result.passed is True
    assert result.reason is None


def test_check_result_fail():
    result = CheckResult.fail("nope")
    assert result.passed is False
    assert result.reason == "nope"


@pytest.mark.asyncio
async def test_cooldown_allows_first_use():
    config = CooldownConfig(rate=3, period=10.0, bucket=BucketScope.USER)
    storage = InMemoryCooldownStorage()
    result = await storage.acquire("user:123", config)
    assert result.allowed is True
    assert result.remaining == 2


@pytest.mark.asyncio
async def test_cooldown_blocks_after_rate():
    config = CooldownConfig(rate=2, period=10.0, bucket=BucketScope.USER)
    storage = InMemoryCooldownStorage()
    await storage.acquire("user:123", config)
    await storage.acquire("user:123", config)
    result = await storage.acquire("user:123", config)
    assert result.allowed is False
    assert result.retry_after > 0


@pytest.mark.asyncio
async def test_cooldown_reset():
    config = CooldownConfig(rate=1, period=10.0, bucket=BucketScope.USER)
    storage = InMemoryCooldownStorage()
    await storage.acquire("user:123", config)
    await storage.reset("user:123")
    result = await storage.acquire("user:123", config)
    assert result.allowed is True


@pytest.mark.asyncio
async def test_cooldown_different_buckets_independent():
    config = CooldownConfig(rate=1, period=10.0, bucket=BucketScope.USER)
    storage = InMemoryCooldownStorage()
    await storage.acquire("user:1", config)
    result = await storage.acquire("user:2", config)
    assert result.allowed is True


def test_check_metadata_is_retained_for_either_decorator_order():
    async def allowed(ctx):
        return CheckResult.ok()

    @check(allowed)
    async def inner_first(ctx):
        pass

    meta = SlashCommandMeta(name="one", description="one", handler=inner_first)
    assert meta.checks == (allowed,)

    outer_first = check(allowed)(meta)
    assert outer_first.checks == (allowed, allowed)


@pytest.mark.asyncio
async def test_executor_rejects_failed_check_before_handler():
    called = False

    async def denied(ctx):
        return CheckResult.fail("denied")

    async def handler():
        nonlocal called
        called = True

    meta = SlashCommandMeta(
        name="protected",
        description="protected",
        handler=handler,
        checks=(denied,),
    )
    ctx = type("Context", (), {})()

    with pytest.raises(CheckFailed, match="denied"):
        await execute_command(meta, ctx, ScopeManager())
    assert called is False


@pytest.mark.asyncio
async def test_executor_enforces_cooldown():
    async def handler():
        pass

    meta = SlashCommandMeta(
        name="limited",
        description="limited",
        handler=handler,
        cooldown=CooldownConfig(rate=1, period=60, bucket=BucketScope.USER),
    )
    ctx = type(
        "Context",
        (),
        {
            "author": type("Author", (), {"id": 123})(),
            "guild_id": None,
            "channel_id": 456,
            "interaction": type("Interaction", (), {"options": [], "resolved": None})(),
        },
    )()

    await execute_command(meta, ctx, ScopeManager())
    with pytest.raises(RateLimited):
        await execute_command(meta, ctx, ScopeManager())
