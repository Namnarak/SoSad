"""Persistent view storage backends.

Allows PersistentView state to survive bot restarts.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ViewStorage(ABC):
    """Abstract storage backend for persistent views."""

    @abstractmethod
    async def save(self, view_id: str, data: dict[str, Any]) -> None: ...

    @abstractmethod
    async def load(self, view_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def delete(self, view_id: str) -> None: ...

    @abstractmethod
    async def cleanup_expired(self, timeout: float) -> int: ...


class InMemoryViewStorage(ViewStorage):
    """In-memory storage (default). Survives within process lifetime."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def save(self, view_id: str, data: dict[str, Any]) -> None:
        self._store[view_id] = data

    async def load(self, view_id: str) -> dict[str, Any] | None:
        return self._store.get(view_id)

    async def delete(self, view_id: str) -> None:
        self._store.pop(view_id, None)

    async def cleanup_expired(self, timeout: float) -> int:
        now = time.time()
        expired = [
            vid for vid, data in self._store.items()
            if now - data.get("created_at", 0) > timeout
        ]
        for vid in expired:
            del self._store[vid]
        return len(expired)


class FileViewStorage(ViewStorage):
    """File-based storage. Views survive bot restarts."""

    def __init__(self, directory: str | Path = "views_data") -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    async def save(self, view_id: str, data: dict[str, Any]) -> None:
        path = self._dir / f"{view_id}.json"
        path.write_text(json.dumps(data, indent=2))

    async def load(self, view_id: str) -> dict[str, Any] | None:
        path = self._dir / f"{view_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    async def delete(self, view_id: str) -> None:
        path = self._dir / f"{view_id}.json"
        if path.exists():
            path.unlink()

    async def cleanup_expired(self, timeout: float) -> int:
        now = time.time()
        count = 0
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                if now - data.get("created_at", 0) > timeout:
                    path.unlink()
                    count += 1
            except (json.JSONDecodeError, OSError):
                pass
        return count


# Global storage instance (defaults to in-memory)
_storage: ViewStorage = InMemoryViewStorage()


def set_view_storage(storage: ViewStorage) -> None:
    global _storage
    _storage = storage


def get_view_storage() -> ViewStorage:
    return _storage


__all__ = [
    "FileViewStorage",
    "InMemoryViewStorage",
    "ViewStorage",
    "get_view_storage",
    "set_view_storage",
]
