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

    # sosad init / sosad new
    for cmd in ("init", "new"):
        p = subparsers.add_parser(cmd, help="Create a new SoSad project")
        p.add_argument("name", help="Project name")
        p.add_argument(
            "--template",
            choices=["gateway", "rest", "components", "minimal"],
            default="gateway",
            help="Project template (default: gateway)",
        )

    args = parser.parse_args()

    if args.command in ("init", "new"):
        scaffold_project(args.name, template=args.template)
    else:
        parser.print_help()


_TEMPLATES: dict[str, str] = {}


def _get_template(name: str) -> str:
    return _TEMPLATES.get(name, _TEMPLATES["gateway"])


def scaffold_project(name: str, template: str = "gateway") -> None:
    """Create a new SoSad project scaffold."""
    project_dir = Path.cwd() / name

    if project_dir.exists():
        print(f"Error: '{name}' already exists")
        sys.exit(1)

    project_dir.mkdir(parents=True)
    plugins_dir = project_dir / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "__init__.py").write_text("")

    # pyproject.toml
    (project_dir / "pyproject.toml").write_text(f'''[project]
name = "{name}"
version = "0.1.0"
description = "A SoSad Discord bot"
requires-python = ">=3.12"
dependencies = [
    "sosad>=0.1.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
''')

    # .env
    (project_dir / ".env").write_text("TOKEN=your-token-here\n")

    # .gitignore
    (project_dir / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.venv/\n.env\n.DS_Store\n"
    )

    # Template-specific files
    if template == "gateway":
        _scaffold_gateway(project_dir, name)
    elif template == "rest":
        _scaffold_rest(project_dir, name)
    elif template == "components":
        _scaffold_components(project_dir, name)
    else:
        _scaffold_minimal(project_dir, name)


def _scaffold_gateway(project_dir: Path, name: str) -> None:
    (project_dir / "bot.py").write_text('''"""Gateway bot with WebSocket connection."""

import hikari
import sosad


class Config(sosad.Settings):
    token: str


config = Config()
bot = sosad.Client(token=config.token, intents=hikari.Intents.ALL_UNPRIVILEGED)


@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")


@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext) -> None:
    await ctx.respond(f"Hello, {ctx.author.mention}!")


@sosad.listen(hikari.StartedEvent)
async def on_ready(event: hikari.StartedEvent) -> None:
    print(f"Logged in as {bot.bot.get_me()}")


@sosad.task(interval=3600)
async def hourly_cleanup() -> None:
    """Run every hour."""
    pass


if __name__ == "__main__":
    bot.run()
''')

    _scaffold_plugin_example(project_dir)


def _scaffold_rest(project_dir: Path, name: str) -> None:
    (project_dir / "bot.py").write_text('''"""REST bot - HTTP-based, serverless-friendly."""

import hikari
import sosad


class Config(sosad.Settings):
    token: str
    public_key: str = ""


config = Config()
bot = sosad.RestBot(
    token=config.token,
    public_key=config.public_key or None,
)


@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")


@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext) -> None:
    await ctx.respond(f"Hello, {ctx.author.mention}!")


@sosad.task(interval=3600)
async def hourly_cleanup() -> None:
    """Run every hour."""
    pass


if __name__ == "__main__":
    bot.run(host="0.0.0.0", port=8080)
''')

    _scaffold_plugin_example(project_dir)

    (project_dir / "Dockerfile").write_text('''FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install uv && uv sync --frozen

CMD ["uv", "run", "bot.py"]
''')

    (project_dir / "wrangler.toml").write_text(f'''name = "{name}"
main = "bot.py"
compatibility_date = "2025-01-01"
''')

    print("  Created Dockerfile + wrangler.toml for deployment")


def _scaffold_components(project_dir: Path, name: str) -> None:
    (project_dir / "bot.py").write_text('''"""Bot with buttons, selects, modals, paginator."""

import hikari
import sosad


class Config(sosad.Settings):
    token: str


config = Config()
bot = sosad.Client(token=config.token, intents=hikari.Intents.ALL_UNPRIVILEGED)


@sosad.slash_command("hello", "Say hello with buttons")
async def hello(ctx: sosad.InteractionContext) -> None:
    view = sosad.View()
    btn = view.button(custom_id="greet", label="Greet", style=hikari.ButtonStyle.SUCCESS)
    btn.on_click(greet_handler)
    btn2 = view.button(custom_id="modal_btn", label="Open Form", style=hikari.ButtonStyle.PRIMARY)
    btn2.on_click(open_modal)
    await ctx.respond("Choose an action:").components(view).send()


async def greet_handler(ctx: sosad.ComponentContext) -> None:
    await ctx.respond().content(f"Hello, {ctx.author.mention}!").ephemeral().send()


async def open_modal(ctx: sosad.ComponentContext) -> None:
    modal = sosad.Modal(title="Feedback")
    modal.text_input("message", label="Your message", style=hikari.TextInputStyle.PARAGRAPH)
    modal.on_submit(submit_feedback)
    await ctx.respond().modal(modal).send()


async def submit_feedback(ctx: sosad.ComponentContext) -> None:
    await ctx.respond().content("Thanks for your feedback!").ephemeral().send()


@sosad.slash_command("pages", "Demo paginator")
async def pages(ctx: sosad.InteractionContext) -> None:
    items = [f"Page {i}: Content here..." for i in range(1, 6)]

    paginator = sosad.components.paginator.Paginator(
        items,
        timeout=60.0,
        show_first_last=True,
    )

    @paginator.on_click("prev")
    async def on_prev(ictx):
        paginator.current -= 1
        await ctx.respond().content(paginator.current_page).components(paginator).send()

    @paginator.on_click("next")
    async def on_next(ictx):
        paginator.current += 1
        await ctx.respond().content(paginator.current_page).components(paginator).send()

    @paginator.on_click("first")
    async def on_first(ictx):
        paginator.current = 0
        await ctx.respond().content(paginator.current_page).components(paginator).send()

    @paginator.on_click("last")
    async def on_last(ictx):
        paginator.current = len(items) - 1
        await ctx.respond().content(paginator.current_page).components(paginator).send()

    paginator.update_page_indicator()
    await ctx.respond().content(paginator.current_page).components(paginator).send()


if __name__ == "__main__":
    bot.run()
''')

    _scaffold_plugin_example(project_dir)


def _scaffold_minimal(project_dir: Path, name: str) -> None:
    (project_dir / "bot.py").write_text('''"""Minimal SoSad bot."""

import hikari
import sosad

bot = sosad.Client(token="TOKEN", intents=hikari.Intents.ALL_UNPRIVILEGED)


@sosad.slash_command("ping", "Pong!")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")


if __name__ == "__main__":
    bot.run()
''')

    (project_dir / ".env").write_text("# Add your token to TOKEN in bot.py\n")


def _scaffold_plugin_example(project_dir: Path) -> None:
    plugins_dir = project_dir / "plugins"
    (plugins_dir / "example.py").write_text('''"""Example plugin."""

import hikari
import sosad


@sosad.slash_command("plugin_cmd", "A command from a plugin")
async def plugin_cmd(ctx: sosad.InteractionContext) -> None:
    await ctx.respond(f"This command is from a plugin! Guild: {ctx.guild_id}")


def setup(client):
    """Called when plugin is loaded."""
    pass
''')

    print()
    print("  uv sync")
    print("  uv run bot.py")
    print()
    print("Edit bot.py and add your token to .env")


__all__ = ["main", "scaffold_project"]
