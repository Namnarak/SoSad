# Quick Start

## Create a project

```bash
sosad new mybot
cd mybot
uv sync
```

The CLI scaffolds a complete project structure:

```
mybot/
├── bot.py              # Entry point
├── .env                # Environment variables
├── .gitignore
├── pyproject.toml
├── plugins/
│   └── example.py      # Example plugin
└── .sosad/             # Framework config
```

## Add your token

Edit `.env`:

```
TOKEN=your-discord-bot-token
```

## Run

```bash
uv run bot.py
```

## Manual setup (without CLI)

```python
# bot.py
import hikari
import sosad

@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")

if __name__ == "__main__":
    bot = sosad.Client(
        token="YOUR_TOKEN_HERE",
        intents=hikari.Intents.ALL_UNPRIVILEGED,
    )
    bot.run()
```

## Using discord.py compat

```python
import sosad.compat as discord
import hikari

bot = discord.Bot(
    command_prefix="!",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
    token="YOUR_TOKEN_HERE",
)

@bot.prefix_command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

bot.run()
```

## Next

- [Commands](commands.md) — slash commands, subcommands, groups
- [Context](context.md) — responding, deferring, editing
- [Components](components.md) — buttons, selects, modals
