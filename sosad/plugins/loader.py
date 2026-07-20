"""Module discovery and import."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any


class PluginLoader:
    """Discovers and loads plugin modules."""

    @staticmethod
    def discover(
        *paths: str | Path,
        pattern: str = "*.py",
    ) -> list[Path]:
        """Find plugin modules by path/glob."""
        result: list[Path] = []
        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                result.append(path)
            elif path.is_dir():
                result.extend(sorted(path.glob(pattern)))
        return result

    @staticmethod
    def load_module(path: Path) -> ModuleType:
        """Import a Python module from a file path."""
        name = f"sosad_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def find_setup(module: ModuleType) -> Callable[..., Any] | None:
        """Look for setup() function or Plugin protocol implementation."""
        setup = getattr(module, "setup", None)
        if callable(setup):
            return setup
        return None


__all__ = ["PluginLoader"]
