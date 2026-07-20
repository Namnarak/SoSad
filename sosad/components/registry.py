"""Component registry — stores button/select/modal handlers.

Also supports persistent views (survive the duration of the view's timeout).
"""

from __future__ import annotations

from typing import Any

from sosad.components.base import ButtonMeta, ModalMeta, SelectMeta


class ComponentRegistry:
    """Stores component interaction handlers by custom_id.

    Also supports persistent views — views that can persist across
    interactions until their timeout expires.
    """

    _instance: ComponentRegistry | None = None

    def __init__(self) -> None:
        self._buttons: dict[str, ButtonMeta] = {}
        self._selects: dict[str, SelectMeta] = {}
        self._modals: dict[str, ModalMeta] = {}
        self._persistent_handlers: dict[str, tuple[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> ComponentRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_button(self, meta: ButtonMeta) -> None:
        self._buttons[meta.custom_id] = meta

    def add_select(self, meta: SelectMeta) -> None:
        self._selects[meta.custom_id] = meta

    def add_modal(self, meta: ModalMeta) -> None:
        self._modals[meta.custom_id] = meta

    def resolve_button(self, custom_id: str) -> ButtonMeta | None:
        return self._buttons.get(custom_id)

    def resolve_select(self, custom_id: str) -> SelectMeta | None:
        return self._selects.get(custom_id)

    def resolve_modal(self, custom_id: str) -> ModalMeta | None:
        return self._modals.get(custom_id)

    def get_handler(self, custom_id: str) -> Any | None:
        meta = self._buttons.get(custom_id) or self._selects.get(custom_id)
        if meta is not None:
            return meta.handler
        parts = custom_id.split(":", 2)
        if len(parts) == 3 and parts[0] == "sv":
            view_id = parts[1]
            comp_id = parts[2]
            from sosad.components.persistent import PersistentView
            view = PersistentView.views.get(view_id)
            if view is not None:
                return view._handlers.get(comp_id)
        return None

    def get_modal_handler(self, custom_id: str) -> Any | None:
        meta = self._modals.get(custom_id)
        if meta is not None:
            return meta.handler
        return None

    def add_persistent_handler(self, view_id: str, comp_id: str, handler: Any) -> None:
        self._persistent_handlers[f"sv:{view_id}:{comp_id}"] = handler

    def remove_persistent_handlers(self, view_id: str) -> None:
        prefix = f"sv:{view_id}:"
        to_remove = [k for k in self._persistent_handlers if k.startswith(prefix)]
        for k in to_remove:
            self._persistent_handlers.pop(k, None)

    def remove(self, custom_id: str) -> bool:
        removed = False
        if custom_id in self._buttons:
            del self._buttons[custom_id]
            removed = True
        if custom_id in self._selects:
            del self._selects[custom_id]
            removed = True
        if custom_id in self._modals:
            del self._modals[custom_id]
            removed = True
        if custom_id in self._persistent_handlers:
            del self._persistent_handlers[custom_id]
            removed = True
        return removed

    @property
    def count(self) -> int:
        return (
            len(self._buttons)
            + len(self._selects)
            + len(self._modals)
            + len(self._persistent_handlers)
        )


# Global registry
_registry = ComponentRegistry()


def get_component_registry() -> ComponentRegistry:
    return _registry


__all__ = ["ComponentRegistry", "get_component_registry"]
