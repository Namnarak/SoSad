"""CLI runner — python -m sosad entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sosad._meta import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sosad",
        description="SoSad Discord Framework",
    )
    parser.add_argument("--version", action="version", version=f"SoSad {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    # sosad new
    new_parser = subparsers.add_parser("new", help="Create a new SoSad project")
    new_parser.add_argument("name", help="Project name")

    args = parser.parse_args()

    if args.command == "new":
        scaffold_project(args.name)
    else:
        parser.print_help()


def scaffold_project(name: str) -> None:
    """Create a new SoSad project scaffold."""
    project_dir = Path.cwd() / name

    if project_dir.exists():
        print(f"Error: '{name}' already exists")
        sys.exit(1)

    project_dir.mkdir(parents=True)
    plugins_dir = project_dir / "plugins"
    plugins_dir.mkdir()

    # pyproject.toml
    (project_dir / "pyproject.toml").write_text(f'''[project]
name = "{name}"
version = "0.1.0"
description = "A SoSad Discord bot"
requires-python = ">=3.12"
dependencies = [
    "sosad>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
''')

    # .env
    (project_dir / ".env").write_text("TOKEN=your-token-here\n")

    # .gitignore
    (project_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\n.env\n")

    # bot.py
    (project_dir / "bot.py").write_text('''import hikari
import sosad


class Config(sosad.Settings):
    token: str


config = Config()
bot = sosad.Client(token=config.token, intents=hikari.Intents.ALL_UNPRIVILEGED)


@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")


if __name__ == "__main__":
    bot.run()
''')

    # plugins/__init__.py
    (plugins_dir / "__init__.py").write_text("")

    # plugins/example.py
    (plugins_dir / "example.py").write_text('''import sosad


@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext) -> None:
    await ctx.respond(f"Hello, {ctx.author.mention}!")


def setup(client):
    """Called when plugin is loaded."""
    pass
''')

    print(f"Created project '{name}'")
    print()
    print(f"  cd {name}")
    print("  uv sync")
    print("  uv run bot.py")
    print()
    print("Edit bot.py and add your token to .env")


__all__ = ["main", "scaffold_project"]
