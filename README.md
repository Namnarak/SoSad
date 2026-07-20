# SoSad

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari).

Python 3.12+ · asyncio · Type hints · Pydantic v2 · Ruff · Pyright strict

## Features

- **Decorator-first API** — `@sosad.slash_command()` on plain functions, no class boilerplate
- **Pipeline middleware** — ASGI-style middleware stack, not hook trees
- **Immutable context** — Frozen dataclass + builder pattern for responses
- **Dependency injection** — Type-hint-based resolution with `inject()` marker
- **Plugin system** — File-based module loading with hot-reload
- **Error handling** — Pipeline-level error catching with typed exceptions
- **Checks & Cooldowns** — Decorator-based pre-conditions and rate limiting
- **Components** — Buttons, Select Menus, Modals
- **Background tasks** — `@sosad.task(interval=300)` periodic task scheduler
- **REST client** — Async HTTP client with rate limit handling and audit log support

## Installation

```bash
pip install sosad
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add sosad
```

## Quick Start

```python
import hikari
import sosad

bot = sosad.Client(
    token="YOUR_TOKEN",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)

@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond().content("Pong!").send()

bot.run()
```

## Commands

### Slash Commands

```python
@sosad.slash_command("hello", "Say hello to someone")
async def hello(
    ctx: sosad.InteractionContext,
    user: hikari.User,
    greeting: str = "Hello",
) -> None:
    await ctx.respond().content(f"{greeting}, {user.mention}!").send()
```

### Command Groups

```python
@sosad.command_group("config", "Bot configuration")
async def config(ctx: sosad.InteractionContext) -> None:
    pass

@sosad.sub_command("config", "set", "Set a config value")
async def config_set(ctx: sosad.InteractionContext, key: str, value: str) -> None:
    await ctx.respond().content(f"Set {key} = {value}").send()
```

### Checks & Permissions

```python
@sosad.slash_command("ban", "Ban a user")
@sosad.check(sosad.is_owner(), sosad.has_permissions(hikari.Permissions.BAN_MEMBERS))
async def ban(ctx: sosad.InteractionContext, user: hikari.User, reason: str = "No reason") -> None:
    await ctx.respond().content(f"Banned {user.mention}: {reason}").send()
```

### Cooldowns

```python
@sosad.slash_command("work", "Earn coins")
@sosad.cooldown(1, 60, bucket=sosad.BucketScope.USER)
async def work(ctx: sosad.InteractionContext) -> None:
    await ctx.respond().content("You earned 10 coins!").send()
```

## Components

### Buttons

```python
@sosad.button("confirm", label="Confirm", style=hikari.ButtonStyle.SUCCESS)
async def on_confirm(ctx: sosad.ComponentContext) -> None:
    await ctx.respond().content("Confirmed!").ephemeral().send()
```

### Select Menus

```python
@sosad.select("color_picker", placeholder="Pick a color", options=[
    {"label": "Red", "value": "red"},
    {"label": "Blue", "value": "blue"},
])
async def on_color(ctx: sosad.ComponentContext) -> None:
    color = ctx.values[0]
    await ctx.respond().content(f"You picked {color}!").send()
```

### Modals

```python
@sosad.modal("feedback_form", title="Send Feedback")
async def on_feedback(ctx: sosad.ComponentContext) -> None:
    await ctx.respond().content("Thanks for your feedback!").ephemeral().send()
```

## Middleware

```python
async def logging_middleware(ctx, next, scope):
    import time
    start = time.monotonic()
    await next(ctx, scope)
    elapsed = (time.monotonic() - start) * 1000
    print(f"{ctx.interaction.command_name} took {elapsed:.1f}ms")

bot.use(logging_middleware)
```

## Dependency Injection

```python
class Database:
    def __init__(self):
        self.connected = True

bot.container.singleton(Database)

@sosad.slash_command("check_db", "Check database status")
async def check_db(
    ctx: sosad.InteractionContext,
    db: Database = sosad.inject(),
) -> None:
    status = "connected" if db.connected else "disconnected"
    await ctx.respond().content(f"Database: {status}").send()
```

## Error Handling

```python
@bot.on_error(sosad.CheckFailed)
async def handle_check_error(error, ctx):
    await ctx.respond().content(str(error)).ephemeral().send()

@bot.on_error(sosad.RateLimited)
async def handle_rate_limit(error, ctx):
    await ctx.respond().content(f"Slow down! Try again in {error.retry_after:.0f}s").ephemeral().send()
```

## Background Tasks

```python
@sosad.task(interval=300, name="cleanup")
async def cleanup_task():
    await db.cleanup_old_records()

@sosad.task(interval=60, once=True, name="startup")
async def startup_task():
    print("Bot is ready!")
```

## Events

```python
@sosad.listen(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    if event.is_user:
        print(f"{event.author.username}: {event.message.content}")
```

## Plugins

```python
# plugins/fun.py
import sosad

@sosad.slash_command("8ball", "Ask the magic 8-ball")
async def eight_ball(ctx: sosad.InteractionContext, question: str) -> None:
    import random
    responses = ["Yes", "No", "Maybe", "Ask again later"]
    await ctx.respond().content(random.choice(responses)).send()

def setup(client):
    """Called when plugin is loaded."""
    pass
```

```python
# bot.py
bot.load_plugins("plugins/")
```

## REST Client

```python
async with sosad.RESTClient(token="YOUR_TOKEN") as api:
    # Send a message
    await api.create_message(channel_id, content="Hello!")

    # Create a webhook
    await api.create_webhook(channel_id, name="My Webhook")

    # Bulk overwrite commands
    await api.bulk_overwrite_global_commands(app_id, commands=[...])
```

## Architecture

```
sosad/
├── core/           # Client, App, constants
├── commands/       # Decorators, registry, router, executor
├── context/        # Immutable InteractionContext + ResponseBuilder
├── middleware/      # ASGI-style pipeline
├── di/             # Container, scoping, inject()
├── events/         # @listen[E], dispatcher
├── checks/         # Check protocol, builtins
├── cooldowns/      # Bucket cooldowns
├── permissions/    # Resolver, decorator
├── errors/         # ErrorPipeline, hierarchy
├── plugins/        # Loader, manager, hot-reload
├── api/            # REST client, rate limits
├── components/     # Buttons, Select Menus, Modals
├── tasks/          # Background task scheduler
├── utils/          # Type helpers
└── cli/            # Entry point
```

## Requirements

- Python 3.12+
- hikari >= 2.0.0
- pydantic >= 2.0

## License

MIT
