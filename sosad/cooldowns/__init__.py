"""Bucket-based rate limiting."""
from sosad.cooldowns.buckets import BucketScope, CooldownConfig, CooldownResult
from sosad.cooldowns.decorator import cooldown
from sosad.cooldowns.storage import CooldownStorage, InMemoryCooldownStorage

__all__ = [
    "BucketScope",
    "CooldownConfig",
    "CooldownResult",
    "CooldownStorage",
    "InMemoryCooldownStorage",
    "cooldown",
]
