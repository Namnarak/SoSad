# Plugin System

Plugins are auto-discovered Python files in the `plugins/` directory.

## Creating a plugin

```python
# plugins/greetings.py
import sosad

class GreetingsPlugin(sosad.Plugin):
    @sosad.slash_command("hello", "Say hello")
    async def hello(self, ctx: sosad.InteractionContext) -> None:
        await ctx.respond("Hello from plugin!")
```

## Plugin auto-discovery

SoSad automatically finds and loads plugins:

```
mybot/
└── plugins/
    ├── __init__.py
    ├── greetings.py
    └── moderation.py
```

```python
bot = sosad.Client(token="...", intents=...)
# Plugins in plugins/ are auto-discovered and loaded
bot.run()
```

## Manual plugin loading

```python
bot = sosad.Client(token="...", intents=...)
bot.load_plugins("my_plugins")
bot.load_extension("my_package.my_plugin")
```

## Plugin lifecycle

```python
class MyPlugin(sosad.Plugin):
    async def on_load(self) -> None:
        """Called when plugin is loaded."""
        await self.setup_database()

    async def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        await self.cleanup()
```

## Plugin config

```python
class MyPlugin(sosad.Plugin):
    class Config:
        prefix: str = "!"
        enabled: bool = True

    @sosad.slash_command("status", "Plugin status")
    async def status(self, ctx: sosad.InteractionContext) -> None:
        await ctx.respond(f"Prefix: {self.config.prefix}")
```

## Load from pip packages

```python
bot.load_extension("sosad_contrib.voice")
bot.load_extension("sosad_contrib.moderation")
```

## Discord.py compat

```python
import sosad.compat as discord

bot = discord.Bot(command_prefix="!", intents=..., token="...")

class MyCog(discord.Cog):
    @discord.app_commands.command(name="ping", description="Ping!")
    async def ping(self, ctx):
        await ctx.send("Pong!")

bot.add_cog(MyCog())
```
