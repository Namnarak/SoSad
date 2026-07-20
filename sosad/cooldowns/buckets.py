"""Cooldown bucket scopes and configuration."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class BucketScope(enum.Enum):
    """Scope for cooldown bucketing."""

    USER = "user"
    GUILD = "guild"
    CHANNEL = "channel"
    MEMBER = "member"  # user + guild combined
    ROLE = "role"


@dataclass(frozen=True, slots=True)
class CooldownConfig:
    """Configuration for a cooldown."""

    rate: int  # number of uses allowed
    period: float  # time window in seconds
    bucket: BucketScope = BucketScope.USER
    retry_after_message: str | None = None


@dataclass(frozen=True, slots=True)
class CooldownResult:
    """Result of a cooldown check."""

    allowed: bool
    remaining: int
    retry_after: float


__all__ = ["BucketScope", "CooldownConfig", "CooldownResult"]
