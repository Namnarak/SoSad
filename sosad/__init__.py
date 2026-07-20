"""SoSad — A modern, modular, type-safe Discord framework built on Hikari."""

from __future__ import annotations

import hikari

from sosad._meta import __version__
from sosad.api import RESTClient
from sosad.checks import (
    CheckResult,
    bot_has_permissions,
    check,
    dm_only,
    guild_only,
    has_permissions,
    has_role,
    in_guild,
    is_owner,
)
from sosad.commands import CommandRegistry, command_group, slash_command, sub_command
from sosad.commands.executor import execute_command
from sosad.components.base import ComponentContext
from sosad.components.modal import Modal, TextInputBuilder
from sosad.components.view import ButtonBuilder, SelectBuilder, View
from sosad.context import InteractionContext, ResponseBuilder
from sosad.cooldowns import BucketScope, CooldownConfig, cooldown
from sosad.core import App, Client
from sosad.core.settings import Settings
from sosad.di import Container, ScopeManager, inject
from sosad.errors import (
    CheckFailed,
    CommandError,
    CommandNotFound,
    ErrorPipeline,
    RateLimited,
    SoSadError,
    SyncError,
)
from sosad.events import EventDispatcher, listen
from sosad.middleware import HandlerFunc, MiddlewareFunc, MiddlewareStack
from sosad.permissions import PermissionResolver, requires_permissions
from sosad.plugins import Plugin, PluginManager
from sosad.tasks import TaskMeta, TaskScheduler, loop, task

__version__ = __version__

# Aliases
app = Client

__all__ = [
    # Core
    "App",
    "Client",
    "app",
    "Settings",
    # Context
    "InteractionContext",
    "ResponseBuilder",
    # Commands
    "CommandRegistry",
    "slash_command",
    "sub_command",
    "command_group",
    "execute_command",
    # Components (View/Builder)
    "View",
    "Modal",
    "ButtonBuilder",
    "SelectBuilder",
    "TextInputBuilder",
    "ComponentContext",
    # Events
    "EventDispatcher",
    "listen",
    # Middleware
    "MiddlewareFunc",
    "HandlerFunc",
    "MiddlewareStack",
    # DI
    "Container",
    "ScopeManager",
    "inject",
    # Checks
    "CheckResult",
    "check",
    "is_owner",
    "has_permissions",
    "has_role",
    "in_guild",
    "dm_only",
    "guild_only",
    "bot_has_permissions",
    # Cooldowns
    "BucketScope",
    "CooldownConfig",
    "cooldown",
    # Permissions
    "PermissionResolver",
    "requires_permissions",
    # Errors
    "SoSadError",
    "CommandError",
    "CommandNotFound",
    "CheckFailed",
    "RateLimited",
    "SyncError",
    "ErrorPipeline",
    # Plugins
    "Plugin",
    "PluginManager",
    # Tasks
    "TaskMeta",
    "TaskScheduler",
    "task",
    "loop",
    # API
    "RESTClient",
    # Re-export hikari
    "hikari",
    # Version
    "__version__",
]
