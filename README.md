# SoSad

**Drop in. Scale up.**

[![PyPI](https://img.shields.io/pypi/v/sosad?color=%237c3aed)](https://pypi.org/project/sosad/)
[![Python](https://img.shields.io/pypi/pyversions/sosad?color=%233498db)](https://pypi.org/project/sosad/)
[![License](https://img.shields.io/pypi/l/sosad?color=%2357F287)](https://github.com/Namnarak/SoSad/blob/main/LICENSE)
![discord.py Compat](https://img.shields.io/badge/discord.py_compat-%E2%89%8890%25-brightgreen)

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari).
Upgrade your bot with minimal rewrites.

```
pip install sosad
```

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

## discord.py Compatibility

≈ 90% of discord.py API is supported out of the box:

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
- Prefix commands (`!ping`) — slash commands only
- Voice / Guild channels / Member editing via compat (use hikari directly)

## What Changes

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

## Performance

| Metric | discord.py | SoSad |
|---|---|---|
| Startup (cold) | ~1.2s | ~0.8s |
| Interaction latency | ~40-80ms | ~40-80ms (same Hikari backend) |
| Memory (idle) | ~45MB | ~35MB |
| REST mode memory | N/A | ~15MB |

*Preliminary, machine-dependent. SoSad's overhead is minimal — it's a thin layer on Hikari.*

## Roadmap

- [x] Gateway bot
- [x] REST bot (serverless-ready)
- [x] Slash commands
- [x] Components (buttons, selects, modals)
- [x] Persistent views + Paginator
- [x] discord.py compat layer (Embed, Colour, File, utils)
- [x] Background task scheduler
- [x] CLI scaffold (`sosad init`)
- [ ] Prefix commands (`!ping`)
- [ ] `discord.app_commands` compat
- [ ] `discord.Object` compat
- [ ] Persist views to database
- [ ] Metrics / OpenTelemetry
- [ ] Webhook support

## Requirements

- Python 3.12+
- hikari >= 2.0.0
- pydantic >= 2.0

## License

MIT
