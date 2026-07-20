"""Global task registry — auto-registers @task decorated functions."""

from __future__ import annotations

from sosad.tasks.base import TaskMeta


class TaskRegistry:
    """Global registry for background tasks.

    Allows auto-discovery of @task decorated functions,
    similar to how commands are auto-registered.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskMeta] = {}

    def register(self, meta: TaskMeta) -> None:
        self._tasks[meta.name] = meta

    def unregister(self, name: str) -> None:
        self._tasks.pop(name, None)

    def get(self, name: str) -> TaskMeta | None:
        return self._tasks.get(name)

    @property
    def all(self) -> dict[str, TaskMeta]:
        return dict(self._tasks)

    def clear(self) -> None:
        self._tasks.clear()

    @property
    def count(self) -> int:
        return len(self._tasks)


_registry = TaskRegistry()


def get_task_registry() -> TaskRegistry:
    return _registry


__all__ = ["TaskRegistry", "get_task_registry"]
