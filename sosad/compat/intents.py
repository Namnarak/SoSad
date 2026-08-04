"""discord.py-compatible mutable intent helpers backed by Hikari."""

from __future__ import annotations

from typing import Any, cast

import hikari


class _IntentsMeta(type):
    """Expose Hikari's intent constants through the compatibility class."""

    def __getattr__(cls, name: str) -> hikari.Intents:
        return cast(hikari.Intents, getattr(hikari.Intents, name))


def _intent_property(name: str) -> property:
    return property(
        lambda instance: instance._get(name),
        lambda instance, enabled: instance._set(name, enabled),
    )


class _MutableIntents:
    def __init__(self, value: int | hikari.Intents = hikari.Intents.NONE) -> None:
        self._value = hikari.Intents(value)

    def to_hikari(self) -> hikari.Intents:
        return self._value

    def __int__(self) -> int:
        return int(self._value)

    def __index__(self) -> int:
        return int(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _MutableIntents):
            return self._value == other._value
        return self._value == other

    def __repr__(self) -> str:
        return f"Intents({int(self)})"

    def __or__(self, other: Any) -> hikari.Intents:
        return self._value | _coerce(other)

    def __and__(self, other: Any) -> hikari.Intents:
        return self._value & _coerce(other)

    def _get(self, name: str) -> bool:
        flag = getattr(hikari.Intents, name, hikari.Intents.NONE)
        return bool(self._value & flag)

    def _set(self, name: str, enabled: bool) -> None:
        flag = getattr(hikari.Intents, name, hikari.Intents.NONE)
        self._value = self._value | flag if enabled else self._value & ~flag

    def _combined(self, *names: str) -> bool:
        return all(self._get(name) for name in names)

    def _set_combined(self, names: tuple[str, ...], enabled: bool) -> None:
        for name in names:
            self._set(name, enabled)

    guilds = _intent_property("GUILDS")
    members = _intent_property("GUILD_MEMBERS")
    bans = _intent_property("GUILD_MODERATION")
    emojis = _intent_property("GUILD_EMOJIS_AND_STICKERS")
    integrations = _intent_property("GUILD_INTEGRATIONS")
    webhooks = _intent_property("GUILD_WEBHOOKS")
    invites = _intent_property("GUILD_INVITES")
    voice_states = _intent_property("GUILD_VOICE_STATES")
    presences = _intent_property("GUILD_PRESENCES")
    guild_messages = _intent_property("GUILD_MESSAGES")
    guild_reactions = _intent_property("GUILD_MESSAGE_REACTIONS")
    guild_typing = _intent_property("GUILD_MESSAGE_TYPING")
    dm_messages = _intent_property("DM_MESSAGES")
    dm_reactions = _intent_property("DM_MESSAGE_REACTIONS")
    dm_typing = _intent_property("DM_MESSAGE_TYPING")
    message_content = _intent_property("MESSAGE_CONTENT")
    guild_scheduled_events = _intent_property("GUILD_SCHEDULED_EVENTS")

    @property
    def messages(self) -> bool:
        return self._combined("GUILD_MESSAGES", "DM_MESSAGES")

    @messages.setter
    def messages(self, enabled: bool) -> None:
        self._set_combined(("GUILD_MESSAGES", "DM_MESSAGES"), enabled)

    @property
    def reactions(self) -> bool:
        return self._combined("GUILD_MESSAGE_REACTIONS", "DM_MESSAGE_REACTIONS")

    @reactions.setter
    def reactions(self, enabled: bool) -> None:
        self._set_combined(("GUILD_MESSAGE_REACTIONS", "DM_MESSAGE_REACTIONS"), enabled)

    @property
    def typing(self) -> bool:
        return self._combined("GUILD_MESSAGE_TYPING", "DM_MESSAGE_TYPING")

    @typing.setter
    def typing(self, enabled: bool) -> None:
        self._set_combined(("GUILD_MESSAGE_TYPING", "DM_MESSAGE_TYPING"), enabled)


def _coerce(value: Any) -> hikari.Intents:
    if isinstance(value, _MutableIntents):
        return value.to_hikari()
    return hikari.Intents(value)


class Intents(metaclass=_IntentsMeta):
    """Mutable facade matching discord.py's ``Intents`` constructors."""

    def __new__(cls, value: int | hikari.Intents = 0) -> _MutableIntents:
        return _MutableIntents(value)

    @classmethod
    def default(cls) -> _MutableIntents:
        return _MutableIntents(hikari.Intents.ALL_UNPRIVILEGED)

    @classmethod
    def all(cls) -> _MutableIntents:
        return _MutableIntents(hikari.Intents.ALL)

    @classmethod
    def none(cls) -> _MutableIntents:
        return _MutableIntents(hikari.Intents.NONE)


__all__ = ["Intents"]
