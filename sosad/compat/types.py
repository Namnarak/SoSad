"""Discord.py-shaped type names backed by Hikari models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import hikari

from sosad.compat.interaction import Interaction


class ButtonStyle:
    """Lowercase discord.py button style names backed by Hikari enum values."""

    primary = hikari.ButtonStyle.PRIMARY
    secondary = hikari.ButtonStyle.SECONDARY
    success = hikari.ButtonStyle.SUCCESS
    danger = hikari.ButtonStyle.DANGER
    link = hikari.ButtonStyle.LINK

    # Common discord.py aliases.
    blurple = primary
    grey = secondary
    gray = secondary
    green = success
    red = danger


ButtonStyle.__members__ = {
    "primary": ButtonStyle.primary,
    "secondary": ButtonStyle.secondary,
    "success": ButtonStyle.success,
    "danger": ButtonStyle.danger,
    "link": ButtonStyle.link,
    "blurple": ButtonStyle.blurple,
    "grey": ButtonStyle.grey,
    "gray": ButtonStyle.gray,
    "green": ButtonStyle.green,
    "red": ButtonStyle.red,
}


class TextStyle:
    """Lowercase discord.py text-input style names backed by Hikari."""

    short = hikari.TextInputStyle.SHORT
    long = hikari.TextInputStyle.PARAGRAPH
    paragraph = long


@dataclass(slots=True)
class SelectOption:
    """A discord.py-compatible select option."""

    label: str
    value: str | None = None
    description: str | None = None
    emoji: Any = None
    default: bool = False

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "label": self.label,
            "value": self.value or self.label,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.emoji is not None:
            data["emoji"] = self.emoji
        if self.default:
            data["default"] = True
        return data


@dataclass(slots=True)
class Game:
    """The small subset of ``discord.Game`` needed by presence updates."""

    name: str

    @property
    def type(self) -> hikari.ActivityType:
        return hikari.ActivityType.PLAYING

    def to_hikari(self) -> hikari.Activity:
        return hikari.Activity(name=self.name, type=hikari.ActivityType.PLAYING)


Activity = hikari.Activity
Locale = hikari.Locale
InteractionCallbackResponse = hikari.InteractionCallbackResponse
WebhookMessage = hikari.Message
InteractionMessage = hikari.Message


class ActivityType:
    playing = hikari.ActivityType.PLAYING
    streaming = hikari.ActivityType.STREAMING
    listening = hikari.ActivityType.LISTENING
    watching = hikari.ActivityType.WATCHING
    custom = hikari.ActivityType.CUSTOM
    competing = hikari.ActivityType.COMPETING


class Status:
    online = hikari.Status.ONLINE
    idle = hikari.Status.IDLE
    dnd = hikari.Status.DO_NOT_DISTURB
    do_not_disturb = dnd
    offline = hikari.Status.OFFLINE


class InteractionType:
    application_command = hikari.InteractionType.APPLICATION_COMMAND
    message_component = hikari.InteractionType.MESSAGE_COMPONENT
    autocomplete = hikari.InteractionType.AUTOCOMPLETE
    modal_submit = hikari.InteractionType.MODAL_SUBMIT


class AllowedMentions:
    """discord.py-style allowed-mentions value object."""

    def __init__(
        self,
        *,
        everyone: bool = True,
        users: bool = True,
        roles: bool = True,
        replied_user: bool = True,
    ) -> None:
        self.everyone = everyone
        self.users = users
        self.roles = roles
        self.replied_user = replied_user

    def none(self) -> AllowedMentions:
        self.everyone = False
        self.users = False
        self.roles = False
        self.replied_user = False
        return self


# Hikari's models are already the useful runtime objects.  These aliases keep
# annotations and ``isinstance`` checks in existing cogs working.
User = hikari.User
Member = hikari.Member
Guild = hikari.Guild
Role = hikari.Role
Message = hikari.Message
Attachment = hikari.Attachment
Emoji = hikari.Emoji
CommandInteraction = hikari.CommandInteraction
ComponentInteraction = hikari.ComponentInteraction
ModalInteraction = hikari.ModalInteraction
TextChannel = hikari.GuildTextChannel
VoiceChannel = hikari.GuildVoiceChannel
PartialMessage = hikari.PartialMessage


class ChannelType:
    """Common discord.py channel type names mapped to Hikari values."""

    text = hikari.ChannelType.GUILD_TEXT
    private = hikari.ChannelType.DM
    voice = hikari.ChannelType.GUILD_VOICE
    group = hikari.ChannelType.GROUP_DM
    category = hikari.ChannelType.GUILD_CATEGORY
    news = hikari.ChannelType.GUILD_NEWS
    news_thread = hikari.ChannelType.GUILD_NEWS_THREAD
    public_thread = hikari.ChannelType.GUILD_PUBLIC_THREAD
    private_thread = hikari.ChannelType.GUILD_PRIVATE_THREAD
    stage_voice = hikari.ChannelType.GUILD_STAGE
    forum = hikari.ChannelType.GUILD_FORUM

Forbidden = hikari.ForbiddenError
NotFound = hikari.NotFoundError
HTTPException = hikari.HTTPError
DiscordException = hikari.HikariError


__all__ = [
    "Attachment",
    "Activity",
    "ActivityType",
    "AllowedMentions",
    "ButtonStyle",
    "ChannelType",
    "CommandInteraction",
    "ComponentInteraction",
    "DiscordException",
    "Emoji",
    "Forbidden",
    "Game",
    "Guild",
    "HTTPException",
    "Interaction",
    "InteractionCallbackResponse",
    "InteractionMessage",
    "InteractionType",
    "Member",
    "Message",
    "ModalInteraction",
    "NotFound",
    "PartialMessage",
    "Role",
    "SelectOption",
    "Status",
    "TextChannel",
    "TextStyle",
    "User",
    "VoiceChannel",
    "WebhookMessage",
]
