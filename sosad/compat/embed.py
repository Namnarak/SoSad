"""discord.py-compatible Embed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import hikari
from hikari.files import URL


@dataclass
class EmbedField:
    name: str
    value: str
    inline: bool = True


class Embed(hikari.Embed):
    """discord.py-compatible Embed.

    Construct and use exactly like discord.py's Embed::

        embed = discord.Embed(
            title="Hello",
            description="This is an embed",
            colour=discord.Colour.blue(),
        )
        embed.add_field(name="Field", value="Value", inline=True)
        embed.set_author(name="Author", icon_url="https://...")
        embed.set_footer(text="Footer", icon_url="https://...")

    Fully compatible with hikari internals — pass to ctx.send(embed=embed).
    """

    def __init__(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        url: str | None = None,
        timestamp: datetime | None = None,
        colour: int | hikari.Colour | None = None,
        color: int | hikari.Colour | None = None,
        **kwargs: Any,
    ) -> None:
        self._embed_fields: list[EmbedField] = []
        super().__init__(
            title=title,
            description=description,
            url=url,
            timestamp=timestamp,
            color=color or colour or kwargs.pop("colour", colour),
        )

    @property
    def fields(self) -> tuple[EmbedField, ...]:
        return tuple(self._embed_fields)

    def add_field(
        self,
        name: str,
        value: str,
        inline: bool = True,
    ) -> Embed:
        """Add a field (inline defaults to True, matching discord.py)."""
        field = EmbedField(name=name, value=str(value), inline=inline)
        # Delegate to hikari for proper rendering
        super().add_field(name=name, value=str(value), inline=inline)
        self._embed_fields.append(field)
        return self

    def set_author(
        self,
        name: str | None = None,
        url: str | None = None,
        icon_url: str | None = None,
    ) -> Embed:
        """Set author (uses icon_url kwarg matching discord.py)."""
        super().set_author(name=name, url=url, icon=icon_url)
        return self

    def set_footer(
        self,
        text: str | None = None,
        icon_url: str | None = None,
    ) -> Embed:
        """Set footer (uses icon_url kwarg matching discord.py)."""
        super().set_footer(text=text, icon=icon_url)
        return self

    def set_image(
        self,
        *,
        url: str | None = None,
        **kwargs: Any,
    ) -> Embed:
        """Set image by URL (discord.py compat)."""
        if url:
            super().set_image(URL(url))
        elif kwargs:
            super().set_image(**kwargs)
        return self

    def set_thumbnail(
        self,
        *,
        url: str | None = None,
        **kwargs: Any,
    ) -> Embed:
        """Set thumbnail by URL (discord.py compat)."""
        if url:
            super().set_thumbnail(URL(url))
        elif kwargs:
            super().set_thumbnail(**kwargs)
        return self

    def remove_field(self, index: int) -> Embed:
        if 0 <= index < len(self._embed_fields):
            self._embed_fields.pop(index)
        return self

    def clear_fields(self) -> Embed:
        self._embed_fields.clear()
        return self

    def set_field_at(
        self,
        index: int,
        name: str,
        value: str,
        inline: bool = True,
    ) -> Embed:
        if 0 <= index < len(self._embed_fields):
            self._embed_fields[index] = EmbedField(name=name, value=value, inline=inline)
        else:
            msg = f"Field index {index} out of range for {len(self._embed_fields)} fields"
            raise IndexError(msg)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "color": self.color,
            "footer": (
                {"text": self.footer.text, "icon_url": self.footer.icon}
                if self.footer else None
            ),
            "image": {"url": self.image.url} if self.image else None,
            "thumbnail": {"url": self.thumbnail.url} if self.thumbnail else None,
            "author": {
                "name": self.author.name,
                "url": self.author.url,
                "icon_url": self.author.icon,
            } if self.author else None,
            "fields": [
                {"name": f.name, "value": f.value, "inline": f.inline}
                for f in self._embed_fields
            ],
        }


__all__ = ["Embed"]
