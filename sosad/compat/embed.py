"""discord.py-compatible Embed."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import hikari


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
        super().__init__(
            title=title,
            description=description,
            url=url,
            timestamp=timestamp,
            color=color or colour,
        )

    def add_field(
        self,
        name: str,
        value: str,
        inline: bool = True,
    ) -> Embed:
        """Add a field (inline defaults to True, matching discord.py)."""
        super().add_field(name=name, value=value, inline=inline)
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

    def remove_field(self, index: int) -> Embed:
        fields = list(self.fields)
        if 0 <= index < len(fields):
            fields.pop(index)
            object.__setattr__(self, "fields", tuple(fields))
        return self

    def clear_fields(self) -> Embed:
        object.__setattr__(self, "fields", ())
        return self

    def set_field_at(
        self,
        index: int,
        name: str,
        value: str,
        inline: bool = True,
    ) -> Embed:
        fields = list(self.fields)
        if 0 <= index < len(fields):
            from dataclasses import dataclass

            @dataclass
            class _Field:
                name: str
                value: str
                inline: bool

            fields[index] = _Field(name=name, value=value, inline=inline)
            object.__setattr__(self, "fields", tuple(fields))
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
                for f in self.fields
            ],
        }


__all__ = ["Embed"]
