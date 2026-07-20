"""Tests for the command system: decorators, registry, router, executor."""

import pytest
import hikari
from sosad.commands.decorators import _extract_options, slash_command, sub_command, command_group
from sosad.commands.models import SlashCommandMeta, SubCommandMeta, CommandGroupMeta, OptionDescriptor
from sosad.commands.registry import CommandRegistry
from sosad.commands.registration import get_registry
from sosad.commands.router import build_handler_args
from sosad.di.scopes import ScopeManager


# ── Option Extraction ──

def test_extract_options_string():
    async def handler(ctx, name: str, count: int = 5): ...
    opts = _extract_options(handler)
    assert len(opts) == 2
    assert opts[0].name == "name"
    assert opts[0].type == hikari.OptionType.STRING
    assert opts[0].required is True
    assert opts[1].name == "count"
    assert opts[1].type == hikari.OptionType.INTEGER
    assert opts[1].required is False


def test_extract_options_skips_ctx():
    async def handler(ctx, name: str): ...
    opts = _extract_options(handler)
    assert len(opts) == 1
    assert opts[0].name == "name"


def test_extract_options_skips_inject():
    from sosad.di.markers import inject
    async def handler(ctx, db: str = inject()): ...
    opts = _extract_options(handler)
    assert len(opts) == 0


def test_extract_options_with_descriptions():
    async def handler(ctx, user: hikari.User, reason: str = "No reason"): ...
    opts = _extract_options(handler, {"user": "The target user", "reason": "Ban reason"})
    assert opts[0].description == "The target user"
    assert opts[1].description == "Ban reason"


def test_extract_options_user_type():
    async def handler(ctx, user: hikari.User): ...
    opts = _extract_options(handler)
    assert opts[0].type == hikari.OptionType.USER


def test_extract_options_role_type():
    async def handler(ctx, role: hikari.Role): ...
    opts = _extract_options(handler)
    assert opts[0].type == hikari.OptionType.ROLE


def test_extract_options_channel_type():
    async def handler(ctx, channel: hikari.GuildChannel): ...
    opts = _extract_options(handler)
    assert opts[0].type == hikari.OptionType.CHANNEL


def test_extract_options_float_type():
    async def handler(ctx, value: float): ...
    opts = _extract_options(handler)
    assert opts[0].type == hikari.OptionType.FLOAT


def test_extract_options_bool_type():
    async def handler(ctx, flag: bool): ...
    opts = _extract_options(handler)
    assert opts[0].type == hikari.OptionType.BOOLEAN


def test_extract_options_no_annotations():
    async def handler(ctx, x): ...
    opts = _extract_options(handler)
    assert len(opts) == 0


# ── Slash Command Decorator ──

def test_slash_command_registers():
    @slash_command("test_ping_1", "A test ping command")
    async def my_handler(ctx): ...

    # @slash_command returns SlashCommandMeta, so my_handler IS the meta
    assert isinstance(my_handler, SlashCommandMeta)

    registry = get_registry()
    assert "test_ping_1" in registry._commands
    meta = registry._commands["test_ping_1"]
    assert meta.name == "test_ping_1"
    assert meta.description == "A test ping command"
    registry.remove("test_ping_1")


def test_slash_command_with_options():
    @slash_command("test_echo", "Echo back")
    async def test_echo(ctx, message: str, count: int = 1): ...
    registry = get_registry()
    meta = registry._commands["test_echo"]
    assert len(meta.options) == 2
    assert meta.options[0].name == "message"
    assert meta.options[1].name == "count"
    registry.remove("test_echo")


def test_slash_command_flags():
    @slash_command("test_opts", "Options test", is_dm_only=True, nsfw=True)
    async def test_opts(ctx): ...
    registry = get_registry()
    meta = registry._commands["test_opts"]
    assert meta.is_dm_only is True
    assert meta.nsfw is True
    assert meta.is_guild_only is False
    registry.remove("test_opts")


# ── Sub Command Decorator ──

def test_sub_command_registers():
    @sub_command("test_cfg", "set", "Set a value")
    async def test_cfg_set(ctx, key: str, value: str): ...
    registry = get_registry()
    assert "test_cfg" in registry._group_subs
    assert "set" in registry._group_subs["test_cfg"]
    meta = registry._group_subs["test_cfg"]["set"]
    assert isinstance(meta, SubCommandMeta)
    assert meta.group == "test_cfg"
    assert meta.name == "set"


# ── Command Group Decorator ──

def test_command_group_registers():
    @command_group("test_group", "A test group")
    async def test_group(ctx): ...
    registry = get_registry()
    assert "test_group" in registry._groups
    meta = registry._groups["test_group"]
    assert isinstance(meta, CommandGroupMeta)
    assert meta.name == "test_group"
    registry.remove("test_group")


# ── Registry ──

def test_registry_add_and_resolve():
    registry = CommandRegistry()
    async def handler(ctx): ...
    meta = SlashCommandMeta(name="ping", description="Pong", handler=handler)
    registry.add(meta)
    assert registry.command_count == 1
    assert "ping" in registry.command_names


def test_registry_remove():
    registry = CommandRegistry()
    async def handler(ctx): ...
    meta = SlashCommandMeta(name="test", description="t", handler=handler)
    registry.add(meta)
    assert registry.remove("test") is True
    assert registry.command_count == 0
    assert registry.remove("nonexistent") is False


def test_registry_clear():
    registry = CommandRegistry()
    async def handler(ctx): ...
    registry.add(SlashCommandMeta(name="a", description="a", handler=handler))
    registry.add(SlashCommandMeta(name="b", description="b", handler=handler))
    registry.clear()
    assert registry.command_count == 0


def test_registry_compute_hash():
    registry = CommandRegistry()
    async def handler(ctx): ...
    registry.add(SlashCommandMeta(name="ping", description="Pong", handler=handler))
    h1 = registry.compute_hash()
    h2 = registry.compute_hash()
    assert h1 == h2
    assert len(h1) == 16


# ── Build Handler Args ──

def test_build_handler_args_skips_ctx():
    """'ctx' param should appear in kwargs, options extracted from interaction."""
    from unittest.mock import MagicMock

    async def handler(ctx, name: str): ...

    # Create a proper mock interaction
    mock_interaction = MagicMock(spec=hikari.CommandInteraction)

    # Create a mock option with proper attributes
    mock_opt = MagicMock()
    mock_opt.name = "name"
    mock_opt.type = hikari.OptionType.STRING
    mock_opt.value = "hello"
    mock_opt.options = None

    mock_interaction.options = [mock_opt]
    mock_interaction.resolved = None

    mock_ctx = MagicMock()
    scope = ScopeManager()

    kwargs = build_handler_args(mock_ctx, mock_interaction, handler, scope)
    assert "ctx" in kwargs
    assert kwargs["ctx"] is mock_ctx
    assert kwargs["name"] == "hello"


def test_build_handler_args_multiple_options():
    from unittest.mock import MagicMock

    async def handler(ctx, name: str, count: int): ...

    mock_interaction = MagicMock(spec=hikari.CommandInteraction)
    opt1 = MagicMock()
    opt1.name = "name"
    opt1.type = hikari.OptionType.STRING
    opt1.value = "hello"
    opt1.options = None
    opt2 = MagicMock()
    opt2.name = "count"
    opt2.type = hikari.OptionType.INTEGER
    opt2.value = 42
    opt2.options = None

    mock_interaction.options = [opt1, opt2]
    mock_interaction.resolved = None

    mock_ctx = MagicMock()
    scope = ScopeManager()

    kwargs = build_handler_args(mock_ctx, mock_interaction, handler, scope)
    assert kwargs["name"] == "hello"
    assert kwargs["count"] == 42
