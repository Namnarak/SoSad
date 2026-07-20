"""Component registry — stores button/select/modal handlers."""

from __future__ import annotations

from sosad.components.base import ButtonMeta, ModalMeta, SelectMeta


class ComponentRegistry:
    """Stores component interaction handlers by custom_id."""

    def __init__(self) -> None:
        self._buttons: dict[str, ButtonMeta] = {}
        self._selects: dict[str, SelectMeta] = {}
        self._modals: dict[str, ModalMeta] = {}

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
        return removed

    @property
    def count(self) -> int:
        return len(self._buttons) + len(self._selects) + len(self._modals)


# Global registry
_registry = ComponentRegistry()


def get_component_registry() -> ComponentRegistry:
    return _registry


__all__ = ["ComponentRegistry", "get_component_registry"]
