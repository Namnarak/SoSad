"""Tests for checks and cooldowns."""

import pytest

from sosad.checks.base import CheckResult
from sosad.cooldowns.buckets import BucketScope, CooldownConfig
from sosad.cooldowns.storage import InMemoryCooldownStorage


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
