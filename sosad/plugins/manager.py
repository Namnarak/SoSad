"""Plugin lifecycle management."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

from sosad.plugins.loader import PluginLoader

logger = logging.getLogger("sosad.plugins")


@dataclass
class LoadedPlugin:
    """A loaded plugin."""

    name: str
    path: Path
    module: ModuleType
    loaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PluginManager:
    """Manages plugin lifecycle.

    Usage::

        manager = PluginManager(client)
        await manager.load_all("plugins/")
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self._loaded: dict[str, LoadedPlugin] = {}

    async def load(self, path: Path) -> LoadedPlugin:
        """Load a single plugin from a file path."""
        module = PluginLoader.load_module(path)
        setup = PluginLoader.find_setup(module)

        if setup is not None:
            result = setup(self._client)
            if hasattr(result, "__await__"):
                await result

        plugin = LoadedPlugin(
            name=path.stem,
            path=path,
            module=module,
        )
        self._loaded[plugin.name] = plugin
        logger.info("Loaded plugin: %s", plugin.name)
        return plugin

    async def unload(self, name: str) -> None:
        """Unload a plugin."""
        plugin = self._loaded.get(name)
        if plugin is None:
            return

        on_unload = getattr(plugin.module, "on_unload", None)
        if callable(on_unload):
            result = on_unload(self._client)
            if hasattr(result, "__await__"):
                await result

        del self._loaded[name]
        logger.info("Unloaded plugin: %s", name)

    async def reload(self, name: str) -> LoadedPlugin | None:
        """Reload a plugin."""
        plugin = self._loaded.get(name)
        if plugin is None:
            return None

        path = plugin.path
        await self.unload(name)
        return await self.load(path)

    async def load_all(self, *paths: str | Path) -> None:
        """Discover and load all plugins from paths."""
        files = PluginLoader.discover(*paths)
        for path in files:
            if path.name.startswith("_"):
                continue
            try:
                await self.load(path)
            except Exception:
                logger.exception("Failed to load plugin: %s", path)

    @property
    def loaded(self) -> dict[str, LoadedPlugin]:
        """Currently loaded plugins."""
        return dict(self._loaded)


__all__ = ["LoadedPlugin", "PluginManager"]
