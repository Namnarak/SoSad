"""Error handling pipeline."""
from sosad.errors.base import (
    CheckFailed,
    CommandError,
    CommandNotFound,
    RateLimited,
    SoSadError,
    SyncError,
)
from sosad.errors.handler import ErrorPipeline

__all__ = [
    "CheckFailed",
    "CommandError",
    "CommandNotFound",
    "ErrorPipeline",
    "RateLimited",
    "SoSadError",
    "SyncError",
]
