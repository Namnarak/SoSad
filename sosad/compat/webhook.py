"""discord.py-compatible Webhook support."""

from __future__ import annotations

import re
from typing import Any

import hikari

_WEBHOOK_URL_RE = re.compile(r"webhooks/(\d+)/([^/]+)")


class Webhook:
    """Represents a Discord webhook.

    Usage::

        webhook = discord.Webhook.from_url("https://discord.com/api/webhooks/...")
        await webhook.send("Hello from webhook!")
    """

    def __init__(self, url: str, *, session: Any = None) -> None:
        self.url = url
        self._session = session
        self._id: int | None = None
        self._token: str | None = None
        self._parse_url(url)

    def _parse_url(self, url: str) -> None:
        match = _WEBHOOK_URL_RE.search(url)
        if match:
            self._id = int(match.group(1))
            self._token = match.group(2)

    @property
    def id(self) -> int:
        if self._id is None:
            msg = "Webhook has no ID"
            raise ValueError(msg)
        return self._id

    @property
    def token(self) -> str:
        if self._token is None:
            msg = "Webhook has no token"
            raise ValueError(msg)
        return self._token

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> Webhook:
        return cls(url, **kwargs)

    async def send(
        self,
        content: str | None = None,
        *,
        embed: hikari.Embed | None = None,
        embeds: list[hikari.Embed] | None = None,
        username: str | None = None,
        avatar_url: str | None = None,
        wait: bool = False,
        **kwargs: Any,
    ) -> hikari.Message | None:
        import aiohttp

        data: dict[str, Any] = {}
        if content:
            data["content"] = content
        if embed:
            data["embeds"] = [embed]
        if embeds:
            data["embeds"] = list(embeds)
        if username:
            data["username"] = username
        if avatar_url:
            data["avatar_url"] = avatar_url

        async with aiohttp.ClientSession() as session:
            params = {"wait": "true"} if wait else {}
            async with session.post(self.url, json=data, params=params) as resp:
                if wait and resp.status == 200:
                    _ = await resp.json()
                    return None
                return None


__all__ = ["Webhook"]
