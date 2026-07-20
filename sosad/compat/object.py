"""discord.py-compatible Object."""

from __future__ import annotations


class Object:
    """Represents a generic Discord object with an ID.

    Usage::

        obj = discord.Object(id=123456789)
        print(obj.id)  # 123456789
    """

    def __init__(self, id: int) -> None:
        self.id = id

    def __int__(self) -> int:
        return self.id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Object):
            return self.id == other.id
        if isinstance(other, int):
            return self.id == other
        return NotImplemented

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return f"<Object id={self.id}>"


__all__ = ["Object"]
