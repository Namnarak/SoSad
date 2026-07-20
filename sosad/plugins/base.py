"""Plugin protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sosad.core.client import Client


@runtime_checkable
class Plugin(Protocol):
    """Optional base protocol for plugins.

    Plugins can implement this protocol or just define a setup() function.
    """

    @staticmethod
    def setup(client: Client) -> None:
        """Called when the plugin is loaded."""
        ...

    @staticmethod
    async def on_load(client: Client) -> None:
        """Async initialization."""
        ...

    @staticmethod
    async def on_unload(client: Client) -> None:
        """Async cleanup."""
        ...


__all__ = ["Plugin"]
