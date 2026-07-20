# Quick Start

## Create a new project

```bash
sosad new mybot
cd mybot
uv sync
```

This creates:

```
mybot/
├── bot.py
├── plugins/
│   ├── __init__.py
│   └── example.py
├── pyproject.toml
└── .env
```

## Add your token

Edit `.env`:

```
TOKEN=your-discord-bot-token-here
```

## Run the bot

```bash
uv run bot.py
```

## Your first command

Edit `bot.py`:

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

## What just happened?

1. `sosad.Settings` reads `TOKEN` from `.env` automatically
2. `@sosad.slash_command` registers a slash command
3. `ctx.respond("Pong!")` sends a response (shortcut syntax)
4. `bot.run()` starts the bot with rate limiting, error handling, and logging enabled
