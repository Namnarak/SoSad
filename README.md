# SoSad

**Drop in. Scale up.**

[![PyPI](https://img.shields.io/pypi/v/sosad?color=%237c3aed)](https://pypi.org/project/sosad/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/Namnarak/SoSad/blob/main/LICENSE)
![Typing: Pyright](https://img.shields.io/badge/typing-pyright--strict-blue)
![Discord API](https://img.shields.io/badge/discord--api-v10-5865F2)

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari) — the fastest, most maintainable Discord library for Python.

SoSad adds high-level features on top of Hikari's solid foundation: dependency injection, middleware pipeline, persistent components, and REST deployment. Designed to ease migration from discord.py while providing modern architecture.

```
pip install sosad
```

## ✨ Features

| | |
|---|---|
| ✓ discord.py Compatibility | Change 1 import line |
| ✓ Native Hikari-first API | Type-safe, FastAPI-style DI |
| ✓ Persistent Views + Paginator | Stateful components with built-in navigation |
| ✓ Background Tasks | `@sosad.task(interval=n)` — cron without the pain |
| ✓ REST + Gateway modes | Serverless-ready or WebSocket |
| ✓ Plugin Auto Discovery | Drop files in `plugins/`, done |
| ✓ CLI Scaffold | `sosad init mybot` — ready in seconds |
| ✓ ASGI Middleware Pipeline | Before, After, Short-circuit |
| ✓ Auto Rate Limiting | Per-route bucket tracking |
| ✓ Type-safe | Pyright strict mode |

## Quick Migration — Before → After

```python
# BEFORE (discord.py)
import discord

bot = discord.Client(intents=discord.Intents.default())

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run("TOKEN")
```

```python
# AFTER (SoSad) — change 1 line
import sosad.compat as discord

bot = discord.Bot(intents=discord.Intents.default())

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

bot.run("TOKEN")
```

**What you get for free:**
- Automatic rate limiting
- Better error handling
- Type safety
- Structured logging
- Plugin loader
- Middleware pipeline
- Background task scheduler

## Architecture

```
  Discord Gateway / HTTP
         │
      Hikari (RESTBot / GatewayBot)
         │
  ┌─────────────────────────────┐
  │          SoSad              │
  ├─────────────────────────────┤
  │  Commands    │  Middleware  │
  ├──────────────┼──────────────┤
  │  Components  │  Scheduler   │
  ├──────────────┼──────────────┤
  │  Plugins     │  DI          │
  ├──────────────┼──────────────┤
  │  Events      │  API Client  │
  └─────────────────────────────┘
         │
    Your Bot Code
```

## discord.py Compatibility

High compatibility with common discord.py APIs:

| discord.py | SoSad compat | Status |
|---|---|---|
| `discord.Client` | `discord.Bot` | ✓ |
| `@bot.command()` | `@bot.command()` | ✓ (slash) |
| `@bot.event` / `@bot.listen` | `@bot.event` / `@bot.listen` | ✓ |
| `@bot.task` | `@bot.task(interval=n)` | ✓ |
| `discord.Embed` | `discord.Embed` | ✓ |
| `discord.Colour` / `discord.Color` | `discord.Colour` / `discord.Color` | ✓ |
| `discord.File` | `discord.File` | ✓ |
| `discord.Intents` | `discord.Intents` | ✓ (re-export) |
| `discord.Permissions` | `discord.Permissions` | ✓ (re-export) |
| `discord.utils` | `discord.get/find/escape/utcnow` | ✓ |
| `discord.ext.commands.Cog` | `discord.Cog` / `@discord.cog` | ✓ |
| `discord.Embed.add_field()` | `discord.Embed.add_field()` | ✓ (inline=True) |
| `discord.Embed.set_author()` | `discord.Embed.set_author()` | ✓ (icon_url) |
| `discord.Embed.set_footer()` | `discord.Embed.set_footer()` | ✓ (icon_url) |
| `ctx.send(embed=...)` | `ctx.send(embed=...)` | ✓ |
| `ctx.send(ephemeral=True)` | `ctx.send(ephemeral=True)` | ✓ |
| `ctx.reply()` / `ctx.edit()` / `ctx.delete()` | `ctx.reply()` / `ctx.edit()` / `ctx.delete()` | ✓ |
| `bot.load_extension()` | `bot.load_extension()` | ✓ |
| `bot.add_cog()` | `bot.add_cog()` | ✓ |

**Not yet supported:**
- `discord.ui` (use SoSad native View/Modal builders)
- `discord.app_commands` (use SoSad native `@sosad.slash_command`)
- Voice / Guild channels / Member editing via compat (use hikari directly)

## Why SoSad?

| Feature | discord.py | SoSad |
|---|---|---|
| Rate limits | Manual / basic | Automatic per-route buckets |
| Error handling | try/except | Pipeline with typed exceptions |
| DI | None | FastAPI-style auto-resolve |
| Middleware | Before/After events | ASGI-style pipeline |
| Plugins | Manual load | Auto-discover `plugins/` |
| Components | Class-based Views | Builder pattern |
| Persistent views | `discord.ui.View(timeout=)` | `PersistentView` with cleanup |
| Paginator | `discord.ui.View` + manual | Built-in `Paginator` |
| Tasks | `tasks.loop` | `@sosad.task(interval=n)` |
| Config | Manual .env | `class Config(sosad.Settings)` |
| REST mode | No | `RestBot` — serverless-ready |
| Type safety | Partial | Full (Pyright strict) |

## Native SoSad API

For new projects, use the SoSad-native API:

```python
import hikari
import sosad

class Config(sosad.Settings):
    token: str

config = Config()
bot = sosad.Client(token=config.token, intents=hikari.Intents.ALL_UNPRIVILEGED)

@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")

bot.run()
```

## Commands

```python
@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext, user: hikari.User) -> None:
    await ctx.respond(f"Hello, {user.mention}!")
```

### Builder Pattern (complex responses)

```python
await (
    ctx.respond()
    .content("Done!")
    .ephemeral()
    .embed(embed)
    .file(file)
    .send()
)
```

## Components

### View with Buttons

```python
view = sosad.View()
view.button(label="Yes", style=hikari.ButtonStyle.SUCCESS, custom_id="yes")
view.button(label="No", style=hikari.ButtonStyle.DANGER, custom_id="no")
await ctx.respond("Confirm?").components(view).send()
```

### Persistent View (stateful, survives across interactions)

```python
view = PersistentView(timeout=60.0)
view.button(custom_id="vote", label="Vote", style=hikari.ButtonStyle.PRIMARY)

@view.on_click("vote")
async def on_vote(ctx):
    await ctx.respond().content("Voted!").ephemeral().send()

await ctx.respond().components(view).send()
```

### Paginator

```python
from sosad.components.paginator import Paginator

pages = ["Page 1 content", "Page 2 content", "Page 3 content"]
paginator = Paginator(pages, timeout=60.0)  # auto-wired

await ctx.respond().content(paginator.current_page).components(paginator).send()
```

### Modal

```python
modal = sosad.Modal(title="Feedback")
modal.text_input("message", label="Your message")
modal.on_submit(submit_handler)
await ctx.respond().modal(modal).send()
```

## Dependency Injection (FastAPI-style)

```python
class Database:
    def __init__(self):
        self.connected = True

bot.container.singleton(Database)

@sosad.slash_command("check_db", "Check database")
async def check_db(ctx: sosad.InteractionContext, db: Database) -> None:
    # db auto-resolved — no inject() needed
    await ctx.respond(f"DB: {'connected' if db.connected else 'down'}")
```

## Middleware

```python
async def logging(ctx, next, scope):
    import time
    start = time.monotonic()
    await next(ctx, scope)
    print(f"{ctx.interaction.command_name}: {(time.monotonic()-start)*1000:.1f}ms")

bot.use(logging)
```

## Background Tasks

```python
@sosad.task(interval=300)
async def cleanup():
    await db.cleanup()

# One-shot task
@sosad.task(interval=10, once=True, name="startup_check")
async def startup():
    await check_api_health()
```

## Auto Plugin Discovery

Just drop files in `plugins/`:

```python
# plugins/fun.py
@sosad.slash_command("8ball", "Ask the magic 8-ball")
async def eight_ball(ctx: sosad.InteractionContext, question: str) -> None:
    import random
    await ctx.respond(random.choice(["Yes", "No", "Maybe"]))
```

No `load_plugins()` needed — SoSad auto-discovers `plugins/` at startup.

## CLI Scaffolding

```bash
sosad init mybot
# or: sosad new mybot --template rest
cd mybot
uv run bot.py
```

Templates: `gateway` (default), `rest`, `components`, `minimal`.

## REST Mode (Serverless)

```python
from sosad import RestBot

bot = RestBot(token="...", public_key="...")
bot.run(host="0.0.0.0", port=8080)
```

Deploy to Cloudflare Workers, Fly.io, Railway, or any HTTP server.

## Settings

```python
class Config(sosad.Settings):
    token: str
    guild_id: int = 0
    debug: bool = False

# Reads from .env automatically
config = Config()
```

## Architecture

| Layer | SoSad |
|---|---|
| Gateway | ✅ |
| REST | ✅ |
| Commands | ✅ |
| Components | ✅ |
| DI | ✅ |
| Middleware | ✅ |
| Plugin Loader | ✅ |
| Scheduler | ✅ |
| Context | ✅ |
| Builder API | ✅ |
| Compat Layer | ✅ |

## Ecosystem

| Package | Description |
|---|---|
| `sosad` | Core framework |
| `sosad-cli` | CLI tools (`sosad init`) |
| `sosad-ext-web` | Web dashboard integration |
| `sosad-ext-views` | Advanced view components |
| `sosad-ext-pagination` | Extended pagination |
| `sosad-ext-cache` | Caching layer |
| `sosad-ext-scheduler` | Advanced task scheduling |

## Roadmap

### Completed
- ✅ Gateway bot
- ✅ REST bot (serverless-ready)
- ✅ Slash commands
- ✅ Components (buttons, selects, modals)
- ✅ Persistent views + Paginator
- ✅ discord.py compat layer (Embed, Colour, File, utils)
- ✅ Background task scheduler
- ✅ CLI scaffold (`sosad init`)
- ✅ Prefix commands (`!ping`)
- ✅ `discord.app_commands` compat
- ✅ `discord.Object` compat

### Planned
- ⏳ Persist views to database
- ⏳ Metrics / OpenTelemetry
- ⏳ Webhook support

## Requirements

- Python 3.12+
- hikari >= 2.0.0
- pydantic >= 2.0

## License

MIT
