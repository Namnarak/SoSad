"""TypeVar helpers and type aliases."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

__all__ = ["T", "T_co"]
