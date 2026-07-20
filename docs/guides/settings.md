# Settings & Config

SoSad uses pydantic-style settings via `BaseSettings`.

## Basic usage

```python
from sosad import Settings

class Config(Settings):
    token: str
    prefix: str = "!"
    debug: bool = False
    database_url: str = "sqlite:///bot.db"
```

## Environment variables

Settings are loaded from `.env` automatically:

```
# .env
TOKEN=your-discord-bot-token
PREFIX=!
DEBUG=true
DATABASE_URL=postgresql://localhost:5432/bot
```

```python
config = Config()
print(config.token)  # "your-discord-bot-token"
```

## Using in commands

```python
@sosad.slash_command("config", "Show config")
async def show_config(ctx: sosad.InteractionContext) -> None:
    config = Config()
    await ctx.respond(f"Prefix: {config.prefix}, Debug: {config.debug}")
```

## Plugin config

```python
class MyPlugin(sosad.Plugin):
    class Config:
        webhook_url: str
        sync_interval: int = 60

    @sosad.slash_command("plugin-status", "Plugin status")
    async def status(self, ctx: sosad.InteractionContext) -> None:
        await ctx.respond(f"Interval: {self.config.sync_interval}s")
```
