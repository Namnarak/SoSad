"""A practical ``discord.py`` compatibility namespace for SoSad.

Existing projects can either use ``import sosad.compat as discord`` or install
SoSad and keep their original ``import discord`` statements.  The latter is
provided by the small top-level shim package in this repository.
"""

from __future__ import annotations

import sys

import hikari

from sosad._meta import __version__
from sosad.compat import app_commands as app_commands
from sosad.compat import errors as errors
from sosad.compat import ui as ui
from sosad.compat import utils as utils
from sosad.compat.app_commands import CommandTree
from sosad.compat.bot import Bot
from sosad.compat.colour import Color, Colour
from sosad.compat.context import Context
from sosad.compat.embed import Embed
from sosad.compat.ext import Cog, cog
from sosad.compat.ext import commands as commands
from sosad.compat.ext import tasks as tasks
from sosad.compat.file import File
from sosad.compat.intents import Intents
from sosad.compat.object import Object as Object
from sosad.compat.types import (
    Activity,
    ActivityType,
    AllowedMentions,
    Attachment,
    ButtonStyle,
    ChannelType,
    CommandInteraction,
    ComponentInteraction,
    DiscordException,
    Emoji,
    Forbidden,
    Game,
    Guild,
    HTTPException,
    Interaction,
    InteractionCallbackResponse,
    InteractionMessage,
    InteractionType,
    Locale,
    Member,
    Message,
    ModalInteraction,
    NotFound,
    PartialMessage,
    Role,
    SelectOption,
    Status,
    TextChannel,
    TextStyle,
    User,
    WebhookMessage,
)
from sosad.compat.utils import (
    escape_markdown,
    escape_markdown_and_mentions,
    escape_mentions,
    find,
    format_dt,
    get,
    snowflake_time,
    utcnow,
)
from sosad.compat.voice import VoiceChannel, VoiceClient, VoiceProtocol, VoiceState
from sosad.compat.webhook import Webhook

Client = Bot
AutoShardedClient = Bot

# This also supports the documented one-line import followed by unchanged
# ``from discord.ext import commands`` statements.
_module = sys.modules[__name__]
sys.modules.setdefault("discord", _module)
sys.modules.setdefault("discord.app_commands", app_commands)
sys.modules.setdefault("discord.errors", errors)
sys.modules.setdefault("discord.ext", sys.modules["sosad.compat.ext"])
sys.modules.setdefault("discord.ext.commands", commands)
sys.modules.setdefault("discord.ext.tasks", tasks)
sys.modules.setdefault("discord.ui", ui)
sys.modules.setdefault("discord.utils", utils)
sys.modules.setdefault("discord.colour", sys.modules["sosad.compat.colour"])
ext = sys.modules["sosad.compat.ext"]


__all__ = [
    "Attachment",
    "Activity",
    "ActivityType",
    "AllowedMentions",
    "AutoShardedClient",
    "Bot",
    "ButtonStyle",
    "ChannelType",
    "Color",
    "Colour",
    "CommandInteraction",
    "CommandTree",
    "ComponentInteraction",
    "Context",
    "Client",
    "Cog",
    "DiscordException",
    "Embed",
    "Emoji",
    "File",
    "Forbidden",
    "Game",
    "Guild",
    "HTTPException",
    "Interaction",
    "InteractionCallbackResponse",
    "InteractionMessage",
    "InteractionType",
    "Intents",
    "Locale",
    "Member",
    "Message",
    "ModalInteraction",
    "NotFound",
    "Object",
    "PartialMessage",
    "PermissionOverwrite",
    "Permissions",
    "Role",
    "SelectOption",
    "Status",
    "TextChannel",
    "TextStyle",
    "User",
    "VoiceChannel",
    "VoiceClient",
    "VoiceProtocol",
    "VoiceState",
    "Webhook",
    "WebhookMessage",
    "__version__",
    "app_commands",
    "commands",
    "cog",
    "errors",
    "escape_markdown",
    "escape_markdown_and_mentions",
    "escape_mentions",
    "ext",
    "find",
    "format_dt",
    "get",
    "tasks",
    "ui",
    "utils",
    "utcnow",
    "snowflake_time",
]


PermissionOverwrite = hikari.PermissionOverwrite
Permissions = hikari.Permissions
