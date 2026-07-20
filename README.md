# SoSad

**Drop in. Scale up.**

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari).
Upgrade your Discord bot without rewriting it.

```
pip install sosad
```

## Quick Migration

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

## What Changes

| Feature | discord.py | SoSad |
|---|---|---|
| Rate limits | Manual / basic | Automatic per-route buckets |
| Error handling | try/except | Pipeline with typed exceptions |
| DI | None | FastAPI-style auto-resolve |
| Middleware | Before/After events | ASGI-style pipeline |
| Plugins | Manual load | Auto-discover `plugins/` |
| Components | Class-based Views | Builder pattern |
| Config | Manual .env | `class Config(sosad.Settings)` |
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

## Components (View/Modal Builders)

```python
view = sosad.View()
view.button(label="Yes", style=hikari.ButtonStyle.SUCCESS, custom_id="yes")
view.button(label="No", style=hikari.ButtonStyle.DANGER, custom_id="no")
await ctx.respond("Confirm?").components(view).send()
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
sosad new mybot
cd mybot
uv run bot.py
```

## Settings

```python
class Config(sosad.Settings):
    token: str
    guild_id: int = 0
    debug: bool = False

# Reads from .env automatically
config = Config()
```

## From Hobby to Production

> "ไม่ได้ย้าย Framework แต่เหมือนอัปเกรด discord.py"

```python
import sosad as discord

bot = discord.Bot(...)

# Production features — enable when ready
bot.enable_plugins()      # auto-discover plugins/
bot.enable_metrics()       # prometheus metrics
bot.enable_tasks()         # background task scheduler
```

## Requirements

- Python 3.12+
- hikari >= 2.0.0
- pydantic >= 2.0

## License

MIT
