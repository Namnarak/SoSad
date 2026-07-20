"""Dynamic module import utilities."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def import_module_from_path(path: Path) -> ModuleType:
    """Import a Python module from a file path."""
    name = path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


__all__ = ["import_module_from_path"]
