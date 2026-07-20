"""Check protocol and result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sosad.context.context import InteractionContext


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result of a check evaluation."""

    passed: bool
    reason: str | None = None

    @classmethod
    def ok(cls) -> CheckResult:
        """Create a passing result."""
        return cls(passed=True)

    @classmethod
    def fail(cls, reason: str) -> CheckResult:
        """Create a failing result."""
        return cls(passed=False, reason=reason)


@runtime_checkable
class CheckFunc(Protocol):
    """A check function protocol."""

    async def __call__(self, ctx: InteractionContext) -> CheckResult: ...


__all__ = ["CheckFunc", "CheckResult"]
