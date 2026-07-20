"""Cooldown storage protocol and in-memory implementation."""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

from sosad.cooldowns.buckets import CooldownConfig, CooldownResult


@runtime_checkable
class CooldownStorage(Protocol):
    """Protocol for cooldown storage backends."""

    async def acquire(self, key: str, config: CooldownConfig) -> CooldownResult: ...
    async def reset(self, key: str) -> None: ...


class InMemoryCooldownStorage:
    """In-memory cooldown storage using timestamps."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}

    async def acquire(self, key: str, config: CooldownConfig) -> CooldownResult:
        """Check and record a cooldown hit."""
        now = time.monotonic()
        window_start = now - config.period

        # Clean old entries
        if key in self._buckets:
            self._buckets[key] = [t for t in self._buckets[key] if t > window_start]
        else:
            self._buckets[key] = []

        entries = self._buckets[key]
        if len(entries) >= config.rate:
            oldest = entries[0]
            retry_after = oldest + config.period - now
            return CooldownResult(
                allowed=False,
                remaining=config.rate - len(entries),
                retry_after=max(retry_after, 0),
            )

        entries.append(now)
        return CooldownResult(
            allowed=True,
            remaining=config.rate - len(entries),
            retry_after=0,
        )

    async def reset(self, key: str) -> None:
        """Reset cooldown for a key."""
        self._buckets.pop(key, None)


__all__ = ["CooldownStorage", "InMemoryCooldownStorage"]
