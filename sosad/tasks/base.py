"""Task base types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskMeta:
    """Metadata for a background task."""

    name: str
    handler: Any
    interval: float  # seconds
    delay: float = 0.0  # initial delay before first run
    once: bool = False  # run only once
    autostart: bool = True
    error_handler: Any = None


@dataclass
class RunningTask:
    """A running task instance."""

    meta: TaskMeta
    task_id: int
    _future: Any = field(default=None, repr=False)

    def cancel(self) -> None:
        if self._future is not None and not self._future.done():
            self._future.cancel()

    @property
    def is_running(self) -> bool:
        return self._future is not None and not self._future.done()


__all__ = ["RunningTask", "TaskMeta"]
