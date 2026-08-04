"""Top-level import shim so SoSad can replace ``discord.py`` imports."""

from __future__ import annotations

from sosad import compat as _compat
from sosad.compat import *  # noqa: F401,F403

__version__ = _compat.__version__
app_commands = _compat.app_commands
commands = _compat.commands
errors = _compat.errors
tasks = _compat.tasks
ui = _compat.ui


def __getattr__(name: str):
    return getattr(_compat, name)
