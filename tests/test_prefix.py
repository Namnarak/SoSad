"""Tests for prefix command system."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from sosad.commands.prefix import (
    PrefixContext,
    PrefixRegistry,
    get_prefix_registry,
    handle_prefix_message,
    prefix_command,
)


class TestPrefixRegistry:
    def test_add_and_resolve(self):
        reg = PrefixRegistry()
        async def handler(ctx):
            pass
        reg.add("ping", handler)
        resolved = reg.resolve("ping")
        assert resolved is handler
        assert reg.resolve("nonexistent") is None

    def test_command_names(self):
        reg = PrefixRegistry()
        async def handler(ctx):
            pass
        reg.add("ping", handler)
        reg.add("pong", handler)
        assert "ping" in reg.command_names
        assert "pong" in reg.command_names
        assert len(reg.command_names) == 2

    def test_remove(self):
        reg = PrefixRegistry()
        async def handler(ctx):
            pass
        reg.add("test", handler)
        assert "test" in reg.command_names
        reg.remove("test")
        assert "test" not in reg.command_names

    def test_remove_nonexistent(self):
        reg = PrefixRegistry()
        reg.remove("nothing")  # Should not raise

    def test_duplicate_add(self):
        reg = PrefixRegistry()
        async def handler1(ctx):
            pass
        async def handler2(ctx):
            pass
        reg.add("cmd", handler1)
        reg.add("cmd", handler2)  # Should overwrite
        assert reg.resolve("cmd") is handler2


class TestPrefixCommandDecorator:
    def test_decorator_registers_handler(self):
        @prefix_command(name="hello")
        async def hello(ctx):
            pass

        reg = get_prefix_registry()
        assert "hello" in reg.command_names
        assert reg.resolve("hello") is not None
        # Cleanup
        reg.remove("hello")

    def test_decorator_default_name(self):
        @prefix_command()
        async def my_func(ctx):
            pass

        reg = get_prefix_registry()
        assert "my_func" in reg.command_names
        reg.remove("my_func")


class TestPrefixContext:
    def test_properties(self):
        mock_event = MagicMock()
        mock_event.message = MagicMock()
        mock_event.message.content = "!ping"
        mock_event.message.author = MagicMock()
        mock_event.message.author.id = 123
        mock_event.message.channel_id = 456
        mock_event.message.guild_id = 789

        ctx = PrefixContext(
            message=mock_event.message,
            client=MagicMock(),
            command_name="ping",
            args=[],
        )
        assert ctx.command_name == "ping"
        assert ctx.args == []

    def test_send(self):
        mock_event = MagicMock()
        mock_event.message = MagicMock()
        mock_event.message.channel_id = 456
        mock_event.message.author = MagicMock()
        mock_event.message.respond = AsyncMock()

        mock_client = MagicMock()

        ctx = PrefixContext(
            message=mock_event.message,
            client=mock_client,
            command_name="test",
            args=[],
        )
        import asyncio
        asyncio.run(ctx.send("Hello"))
        mock_event.message.respond.assert_called_once_with("Hello")


class TestHandlePrefixMessage:
    def test_basic_message(self):
        reg = PrefixRegistry()
        handler = AsyncMock()
        reg.add("ping", handler)

        mock_msg = MagicMock()
        mock_msg.content = "!ping"
        mock_msg.author = MagicMock()
        mock_msg.author.is_bot = False
        mock_msg.author.is_system = False
        mock_msg.channel_id = 111
        mock_msg.guild_id = 222

        mock_client = MagicMock()

        import asyncio
        asyncio.run(handle_prefix_message(mock_msg, mock_client, prefix="!", registry=reg))
        handler.assert_called_once()

    def test_wrong_prefix(self):
        reg = PrefixRegistry()
        handler = AsyncMock()
        reg.add("ping", handler)

        mock_msg = MagicMock()
        mock_msg.content = "?ping"
        mock_msg.author = MagicMock()
        mock_msg.author.is_bot = False
        mock_msg.author.is_system = False

        import asyncio
        asyncio.run(handle_prefix_message(mock_msg, MagicMock(), prefix="!", registry=reg))
        handler.assert_not_called()

    def test_unknown_command(self):
        reg = PrefixRegistry()
        handler = AsyncMock()
        reg.add("known", handler)

        mock_msg = MagicMock()
        mock_msg.content = "!unknown"
        mock_msg.author = MagicMock()
        mock_msg.author.bot = False

        import asyncio
        asyncio.run(handle_prefix_message(mock_msg, MagicMock(), prefix="!", registry=reg))
        handler.assert_not_called()

    def test_bot_message_ignored(self):
        reg = PrefixRegistry()
        handler = AsyncMock()
        reg.add("ping", handler)

        mock_msg = MagicMock()
        mock_msg.content = "!ping"
        mock_msg.author = MagicMock()
        mock_msg.author.is_bot = True
        mock_msg.author.is_system = False

        import asyncio
        asyncio.run(handle_prefix_message(mock_msg, MagicMock(), prefix="!", registry=reg))
        handler.assert_not_called()

    def test_with_args(self):
        reg = PrefixRegistry()
        handler = AsyncMock()
        reg.add("echo", handler)

        mock_msg = MagicMock()
        mock_msg.content = '!echo hello world'
        mock_msg.author = MagicMock()
        mock_msg.author.is_bot = False
        mock_msg.author.is_system = False
        mock_msg.channel_id = 1
        mock_msg.guild_id = 2

        mock_client = MagicMock()

        import asyncio
        asyncio.run(handle_prefix_message(mock_msg, mock_client, prefix="!", registry=reg))
        handler.assert_called_once()
        ctx = handler.call_args[0][0]
        assert ctx.args == ["hello", "world"]
        assert ctx.command_name == "echo"

    def test_no_prefix_match_bot_prefix(self):
        reg = PrefixRegistry()
        handler = AsyncMock()
        reg.add("ping", handler)

        mock_msg = MagicMock()
        mock_msg.content = "not a command"
        mock_msg.author = MagicMock()

        import asyncio
        asyncio.run(handle_prefix_message(mock_msg, MagicMock(), prefix="!", registry=reg))
        handler.assert_not_called()
