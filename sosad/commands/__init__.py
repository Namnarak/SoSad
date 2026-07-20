"""Command system."""
from sosad.commands.decorators import command_group, slash_command, sub_command
from sosad.commands.registry import CommandRegistry

__all__ = ["CommandRegistry", "command_group", "slash_command", "sub_command"]
