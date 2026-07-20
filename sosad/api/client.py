"""REST client wrapper for Discord API with rate limit handling."""

from __future__ import annotations

import asyncio
import io
import json
import logging
from typing import Any

import aiohttp

from sosad.api.rate_limit import RateLimitState, parse_route
from sosad.api.types import (
    APIError,
    HTTPMethod,
    RESTResponse,
)

logger = logging.getLogger("sosad.api")

BASE_URL = "https://discord.com/api/v10"


class RESTClient:
    """Async REST client for Discord API with rate limit handling.

    Usage::

        async with RESTClient(token="...") as client:
            msg = await client.create_message(channel_id, content="Hello!")
    """

    def __init__(
        self,
        token: str,
        *,
        session: aiohttp.ClientSession | None = None,
        base_url: str = BASE_URL,
    ) -> None:
        self._token = token
        self._base_url = base_url
        self._session: aiohttp.ClientSession | None = session
        self._own_session = session is None
        self._rate_limits = RateLimitState()
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> RESTClient:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._own_session and self._session is not None:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("Client not started. Use 'async with' or call start().")
        return self._session

    def _headers(
        self,
        content_type: str | None = "application/json",
        reason: str | None = None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Build request headers."""
        headers: dict[str, str] = {
            "Authorization": f"Bot {self._token}",
            "User-Agent": "SoSad (https://github.com/sosad-framework)",
        }
        if content_type is not None:
            headers["Content-Type"] = content_type
        if reason is not None:
            headers["X-Audit-Log-Reason"] = reason
        if extra:
            headers.update(extra)
        return headers

    async def _request(
        self,
        method: HTTPMethod,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
        files: list[tuple[str, io.IOBase, str]] | None = None,
        reason: str | None = None,
        query: dict[str, str] | None = None,
    ) -> RESTResponse:
        """Execute a REST request with rate limit handling."""
        url = f"{self._base_url}{path}"
        route = parse_route(method.value, path)

        # Check rate limits
        is_limited, retry_after = self._rate_limits.is_rate_limited(route)
        if is_limited:
            logger.info("Rate limited on %s, waiting %.2fs", route, retry_after)
            await asyncio.sleep(retry_after)

        headers = self._headers(
            content_type="application/json" if json_data is not None and files is None else None,
            reason=reason,
        )

        async with self._lock:
            try:
                if files or form_data:
                    # Multipart form data
                    data = aiohttp.FormData()
                    if form_data:
                        for key, value in form_data.items():
                            data.add_field(key, str(value))
                    if files:
                        for name, file_obj, filename in files:
                            data.add_field(name, file_obj, filename=filename)
                    if json_data:
                        data.add_field(
                            "payload_json",
                            json.dumps(json_data),
                            content_type="application/json",
                        )
                    headers.pop("Content-Type", None)

                    async with self.session.request(
                        method.value,
                        url,
                        headers=headers,
                        data=data,
                        params=query,
                    ) as resp:
                        return await self._handle_response(resp, route)
                elif json_data is not None:
                    async with self.session.request(
                        method.value,
                        url,
                        headers=headers,
                        json=json_data,
                        params=query,
                    ) as resp:
                        return await self._handle_response(resp, route)
                else:
                    async with self.session.request(
                        method.value,
                        url,
                        headers=headers,
                        params=query,
                    ) as resp:
                        return await self._handle_response(resp, route)
            except aiohttp.ClientError as exc:
                logger.error("Request failed: %s %s - %s", method.value, path, exc)
                return RESTResponse(
                    status=0,
                    headers={},
                    error=APIError(code=0, message=str(exc)),
                )

    async def _handle_response(
        self,
        resp: aiohttp.ClientResponse,
        route: str,
    ) -> RESTResponse:
        """Handle a response, updating rate limits."""
        resp_headers = dict(resp.headers)
        self._rate_limits.update_from_headers(route, resp_headers)
        self._rate_limits.consume(route)

        # Handle rate limit response
        if resp.status == 429:
            retry_after = float(resp_headers.get("Retry-After", "1"))
            is_global = resp_headers.get("X-RateLimit-Global") == "true"
            if is_global:
                self._rate_limits.mark_global_rate_limited(retry_after)
            logger.warning("Rate limited: %s (retry after %.2fs)", route, retry_after)
            await asyncio.sleep(retry_after)
            return RESTResponse(
                status=429,
                headers=resp_headers,
                error=APIError(code=429, message="Rate limited"),
            )

        # Parse response body
        data = None
        error = None
        try:
            text = await resp.text()
            if text:
                data = json.loads(text)
        except (json.JSONDecodeError, aiohttp.ClientError):
            pass

        if not resp.ok:
            if isinstance(data, dict) and "code" in data:
                error = APIError(
                    code=data.get("code", 0),
                    message=data.get("message", "Unknown error"),
                    errors=data.get("errors"),
                )
            else:
                error = APIError(code=resp.status, message=f"HTTP {resp.status}")

        return RESTResponse(
            status=resp.status,
            headers=resp_headers,
            data=data,
            error=error,
        )

    # ── Channel Endpoints ──

    async def get_channel(self, channel_id: str) -> RESTResponse:
        """GET /channels/{channel.id}"""
        return await self._request(HTTPMethod.GET, f"/channels/{channel_id}")

    async def modify_channel(
        self,
        channel_id: str,
        *,
        name: str | None = None,
        topic: str | None = None,
        nsfw: bool | None = None,
        rate_limit_per_user: int | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> RESTResponse:
        """PATCH /channels/{channel.id}"""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if topic is not None:
            payload["topic"] = topic
        if nsfw is not None:
            payload["nsfw"] = nsfw
        if rate_limit_per_user is not None:
            payload["rate_limit_per_user"] = rate_limit_per_user
        payload.update(kwargs)
        return await self._request(
            HTTPMethod.PATCH,
            f"/channels/{channel_id}",
            json_data=payload,
            reason=reason,
        )

    async def delete_channel(
        self,
        channel_id: str,
        *,
        reason: str | None = None,
    ) -> RESTResponse:
        """DELETE /channels/{channel.id}"""
        return await self._request(
            HTTPMethod.DELETE,
            f"/channels/{channel_id}",
            reason=reason,
        )

    # ── Message Endpoints ──

    async def get_messages(
        self,
        channel_id: str,
        *,
        limit: int = 50,
        before: str | None = None,
        after: str | None = None,
        around: str | None = None,
    ) -> RESTResponse:
        """GET /channels/{channel.id}/messages"""
        query: dict[str, str] = {"limit": str(min(limit, 100))}
        if before:
            query["before"] = before
        if after:
            query["after"] = after
        if around:
            query["around"] = around
        return await self._request(
            HTTPMethod.GET,
            f"/channels/{channel_id}/messages",
            query=query,
        )

    async def create_message(
        self,
        channel_id: str,
        *,
        content: str | None = None,
        embeds: list[dict[str, Any]] | None = None,
        tts: bool = False,
        flags: int | None = None,
        allowed_mentions: dict[str, Any] | None = None,
        components: list[dict[str, Any]] | None = None,
        sticker_ids: list[str] | None = None,
        files: list[tuple[str, io.IOBase, str]] | None = None,
        payload_json: dict[str, Any] | None = None,
    ) -> RESTResponse:
        """POST /channels/{channel.id}/messages"""
        payload: dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if embeds is not None:
            payload["embeds"] = embeds
        if tts:
            payload["tts"] = True
        if flags is not None:
            payload["flags"] = flags
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions
        if components is not None:
            payload["components"] = components
        if sticker_ids is not None:
            payload["sticker_ids"] = sticker_ids

        if files:
            return await self._request(
                HTTPMethod.POST,
                f"/channels/{channel_id}/messages",
                json_data=payload or None,
                files=files,
            )
        return await self._request(
            HTTPMethod.POST,
            f"/channels/{channel_id}/messages",
            json_data=payload or payload_json,
        )

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        content: str | None = None,
        embeds: list[dict[str, Any]] | None = None,
        flags: int | None = None,
        components: list[dict[str, Any]] | None = None,
    ) -> RESTResponse:
        """PATCH /channels/{channel.id}/messages/{message.id}"""
        payload: dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if embeds is not None:
            payload["embeds"] = embeds
        if flags is not None:
            payload["flags"] = flags
        if components is not None:
            payload["components"] = components
        return await self._request(
            HTTPMethod.PATCH,
            f"/channels/{channel_id}/messages/{message_id}",
            json_data=payload,
        )

    async def delete_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        reason: str | None = None,
    ) -> RESTResponse:
        """DELETE /channels/{channel.id}/messages/{message.id}"""
        return await self._request(
            HTTPMethod.DELETE,
            f"/channels/{channel_id}/messages/{message_id}",
            reason=reason,
        )

    async def bulk_delete_messages(
        self,
        channel_id: str,
        message_ids: list[str],
        *,
        reason: str | None = None,
    ) -> RESTResponse:
        """POST /channels/{channel.id}/messages/bulk-delete"""
        return await self._request(
            HTTPMethod.POST,
            f"/channels/{channel_id}/messages/bulk-delete",
            json_data={"messages": message_ids},
            reason=reason,
        )

    # ── Guild Endpoints ──

    async def get_guild(
        self,
        guild_id: str,
        *,
        with_counts: bool = False,
    ) -> RESTResponse:
        """GET /guilds/{guild.id}"""
        query: dict[str, str] = {}
        if with_counts:
            query["with_counts"] = "true"
        return await self._request(
            HTTPMethod.GET,
            f"/guilds/{guild_id}",
            query=query,
        )

    # ── Webhook Endpoints ──

    async def create_webhook(
        self,
        channel_id: str,
        *,
        name: str,
        avatar: str | None = None,
        reason: str | None = None,
    ) -> RESTResponse:
        """POST /channels/{channel.id}/webhooks"""
        payload: dict[str, Any] = {"name": name}
        if avatar is not None:
            payload["avatar"] = avatar
        return await self._request(
            HTTPMethod.POST,
            f"/channels/{channel_id}/webhooks",
            json_data=payload,
            reason=reason,
        )

    # ── Application Command Endpoints ──

    async def get_global_commands(
        self,
        application_id: str,
    ) -> RESTResponse:
        """GET /applications/{application.id}/commands"""
        return await self._request(
            HTTPMethod.GET,
            f"/applications/{application_id}/commands",
        )

    async def create_global_command(
        self,
        application_id: str,
        *,
        name: str,
        description: str,
        type: int = 1,
        options: list[dict[str, Any]] | None = None,
        default_member_permissions: str | None = None,
        dm_permission: bool = True,
        nsfw: bool = False,
    ) -> RESTResponse:
        """POST /applications/{application.id}/commands"""
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "type": type,
            "dm_permission": dm_permission,
            "nsfw": nsfw,
        }
        if options is not None:
            payload["options"] = options
        if default_member_permissions is not None:
            payload["default_member_permissions"] = default_member_permissions
        return await self._request(
            HTTPMethod.POST,
            f"/applications/{application_id}/commands",
            json_data=payload,
        )

    async def edit_global_command(
        self,
        application_id: str,
        command_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        options: list[dict[str, Any]] | None = None,
        default_member_permissions: str | None = None,
        dm_permission: bool | None = None,
        nsfw: bool | None = None,
    ) -> RESTResponse:
        """PATCH /applications/{application.id}/commands/{command.id}"""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if options is not None:
            payload["options"] = options
        if default_member_permissions is not None:
            payload["default_member_permissions"] = default_member_permissions
        if dm_permission is not None:
            payload["dm_permission"] = dm_permission
        if nsfw is not None:
            payload["nsfw"] = nsfw
        return await self._request(
            HTTPMethod.PATCH,
            f"/applications/{application_id}/commands/{command_id}",
            json_data=payload,
        )

    async def delete_global_command(
        self,
        application_id: str,
        command_id: str,
    ) -> RESTResponse:
        """DELETE /applications/{application.id}/commands/{command.id}"""
        return await self._request(
            HTTPMethod.DELETE,
            f"/applications/{application_id}/commands/{command_id}",
        )

    async def bulk_overwrite_global_commands(
        self,
        application_id: str,
        commands: list[dict[str, Any]],
    ) -> RESTResponse:
        """PUT /applications/{application.id}/commands

        Bulk overwrite all global commands.
        """
        return await self._request(
            HTTPMethod.PUT,
            f"/applications/{application_id}/commands",
            json_data=commands,
        )

    # ── Guild Command Endpoints ──

    async def get_guild_commands(
        self,
        application_id: str,
        guild_id: str,
    ) -> RESTResponse:
        """GET /applications/{application.id}/guilds/{guild.id}/commands"""
        return await self._request(
            HTTPMethod.GET,
            f"/applications/{application_id}/guilds/{guild_id}/commands",
        )

    async def bulk_overwrite_guild_commands(
        self,
        application_id: str,
        guild_id: str,
        commands: list[dict[str, Any]],
    ) -> RESTResponse:
        """PUT /applications/{application.id}/guilds/{guild.id}/commands"""
        return await self._request(
            HTTPMethod.PUT,
            f"/applications/{application_id}/guilds/{guild_id}/commands",
            json_data=commands,
        )

    # ── Interaction Response Endpoints ──

    async def create_interaction_response(
        self,
        interaction_id: str,
        interaction_token: str,
        *,
        type: int,
        data: dict[str, Any] | None = None,
    ) -> RESTResponse:
        """POST /interactions/{interaction.id}/{interaction.token}/callback"""
        payload: dict[str, Any] = {"type": type}
        if data is not None:
            payload["data"] = data
        return await self._request(
            HTTPMethod.POST,
            f"/interactions/{interaction_id}/{interaction_token}/callback",
            json_data=payload,
        )

    async def edit_interaction_response(
        self,
        application_id: str,
        interaction_token: str,
        *,
        content: str | None = None,
        embeds: list[dict[str, Any]] | None = None,
        components: list[dict[str, Any]] | None = None,
        flags: int | None = None,
    ) -> RESTResponse:
        """PATCH /webhooks/{application.id}/{interaction.token}/messages/@original"""
        payload: dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if embeds is not None:
            payload["embeds"] = embeds
        if components is not None:
            payload["components"] = components
        if flags is not None:
            payload["flags"] = flags
        return await self._request(
            HTTPMethod.PATCH,
            f"/webhooks/{application_id}/{interaction_token}/messages/@original",
            json_data=payload,
        )

    async def create_followup_message(
        self,
        application_id: str,
        interaction_token: str,
        *,
        content: str | None = None,
        embeds: list[dict[str, Any]] | None = None,
        tts: bool = False,
        flags: int | None = None,
        components: list[dict[str, Any]] | None = None,
        files: list[tuple[str, io.IOBase, str]] | None = None,
    ) -> RESTResponse:
        """POST /webhooks/{application.id}/{interaction.token}"""
        payload: dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if embeds is not None:
            payload["embeds"] = embeds
        if tts:
            payload["tts"] = True
        if flags is not None:
            payload["flags"] = flags
        if components is not None:
            payload["components"] = components

        if files:
            return await self._request(
                HTTPMethod.POST,
                f"/webhooks/{application_id}/{interaction_token}",
                json_data=payload or None,
                files=files,
            )
        return await self._request(
            HTTPMethod.POST,
            f"/webhooks/{application_id}/{interaction_token}",
            json_data=payload,
        )


__all__ = ["RESTClient", "BASE_URL"]
