"""Internal constants and sentinels."""

from __future__ import annotations

import enum


class _MissingType:
    """Sentinel for missing default values."""

    _instance: _MissingType | None = None

    def __new__(cls) -> _MissingType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<MISSING>"

    def __bool__(self) -> bool:
        return False


MISSING = _MissingType()


class LogLevel(enum.Enum):
    """Log level for the framework."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


__all__ = ["MISSING", "LogLevel"]
