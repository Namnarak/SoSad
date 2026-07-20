# SoSad

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari).

Python 3.12+ · asyncio · Type hints · Pydantic v2 · Ruff · Pyright strict

## Features

- **FastAPI-style DI** — Auto-resolve dependencies from type annotations, no `inject()` needed
- **Response Builder** — `ctx.respond("Pong!")` shortcut OR builder pattern for complex responses
- **Pipeline middleware** — ASGI-style middleware stack, not hook trees
- **View/Modal builders** — Build components dynamically, not with decorators
- **Auto plugin discovery** — Just drop `.py` files in `plugins/`
- **Settings** — `class Config(sosad.Settings)` with auto `.env` loading
- **CLI scaffolding** — `sosad new mybot` creates a ready-to-run project
- **Error handling** — Pipeline-level error catching with typed exceptions
- **Background tasks** — `@sosad.task(interval=300)` periodic task scheduler
- **REST client** — Async HTTP client with rate limit handling

## Quick Start

```bash
uv add sosad
sosad new mybot
cd mybot
uv run bot.py
```

## Usage

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

### Command Groups

```python
@sosad.command_group("config", "Bot configuration")
async def config(ctx: sosad.InteractionContext) -> None:
    pass

@sosad.sub_command("config", "set", "Set a value")
async def config_set(ctx: sosad.InteractionContext, key: str, value: str) -> None:
    await ctx.respond(f"Set {key} = {value}")
```

## Dependency Injection (FastAPI-style)

```python
class Database:
    def __init__(self):
        self.connected = True

bot.container.singleton(Database)

@sosad.slash_command("check_db", "Check database")
async def check_db(ctx: sosad.InteractionContext, db: Database) -> None:
    # db is auto-resolved from container — no inject() needed
    await ctx.respond(f"DB: {'connected' if db.connected else 'down'}")
```

## Components (View/Modal Builders)

### Buttons

```python
view = sosad.View()
view.button(label="Yes", style=hikari.ButtonStyle.SUCCESS, custom_id="yes")
view.button(label="No", style=hikari.ButtonStyle.DANGER, custom_id="no")

await ctx.respond("Confirm?").components(view).send()
```

### Select Menus

```python
view = sosad.View()
view.select(custom_id="color", placeholder="Pick a color") \
    .add_option("Red", "red") \
    .add_option("Blue", "blue")

await ctx.respond("Choose:").components(view).send()
```

### Modals

```python
modal = sosad.Modal(title="Feedback")
modal.text_input("name", label="Your Name")
modal.text_input("bio", label="Bio", style=hikari.TextInputStyle.PARAGRAPH)

await ctx.respond().modal(modal).send()
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

## Checks & Cooldowns

```python
@sosad.slash_command("ban", "Ban a user")
@sosad.check(sosad.has_permissions(hikari.Permissions.BAN_MEMBERS))
@sosad.cooldown(1, 60, bucket=sosad.BucketScope.USER)
async def ban(ctx: sosad.InteractionContext, user: hikari.User) -> None:
    await ctx.respond(f"Banned {user.mention}")
```

## Error Handling

```python
@bot.on_error(sosad.CheckFailed)
async def on_check(error, ctx):
    await ctx.respond(str(error)).ephemeral()
```

## Background Tasks

```python
@sosad.task(interval=300)
async def cleanup():
    await db.cleanup()

@sosad.task(interval=60, once=True)
async def startup():
    print("Ready!")
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

## Settings

```python
class Config(sosad.Settings):
    token: str
    guild_id: int = 0
    debug: bool = False

# Reads from .env automatically
config = Config()
```

## CLI

```bash
# Create a new project
sosad new mybot

# Output:
# mybot/
#  ├── bot.py
#  ├── plugins/
#  ├── config.py
#  ├── pyproject.toml
#  └── .env
```

## Requirements

- Python 3.12+
- hikari >= 2.0.0
- pydantic >= 2.0
- pydantic-settings >= 2.0

## License

MIT
