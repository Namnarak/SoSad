"""Global registry populated by decorators at import time."""

from __future__ import annotations

from sosad.commands.models import CommandGroupMeta, SlashCommandMeta, SubCommandMeta
from sosad.commands.registry import CommandRegistry

# Global registry — decorators push metadata here at import time
_registry = CommandRegistry()


def register_command(
    meta: SlashCommandMeta | CommandGroupMeta | SubCommandMeta,
) -> None:
    """Called by decorators to add metadata to the registry."""
    _registry.add(meta)


def get_registry() -> CommandRegistry:
    """Get the global command registry."""
    return _registry


__all__ = ["get_registry", "register_command"]
