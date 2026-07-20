# Commands

## Slash Commands

```python
import sosad

@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")
```

### With options

```python
@sosad.slash_command("greet", "Greet someone")
async def greet(
    ctx: sosad.InteractionContext,
    name: str = sosad.annotations.String(description="Who to greet"),
    age: int = sosad.annotations.Integer(description="Their age", min_value=0),
) -> None:
    await ctx.respond(f"Hello {name}, age {age}!")
```

### With autocomplete

```python
@sosad.slash_command("search", "Search items")
async def search(
    ctx: sosad.InteractionContext,
    query: str = sosad.annotations.String(description="Search query", autocomplete=True),
) -> None:
    await ctx.respond(f"Searching for {query}...")

@search.autocomplete("query")
async def autocomplete_query(ctx: sosad.InteractionContext, current: str) -> list[str]:
    return ["apple", "banana", "cherry"]
```

## Subcommands

```python
from sosad import command_group

config = command_group("config", "Configuration commands")

@config.sub_command("view", "View config")
async def config_view(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Config: ...")

@config.sub_command("set", "Set config value")
async def config_set(
    ctx: sosad.InteractionContext,
    key: str = sosad.annotations.String(description="Config key"),
    value: str = sosad.annotations.String(description="Config value"),
) -> None:
    await ctx.respond(f"Set {key} = {value}")
```

## Prefix Commands

```python
from sosad.commands.prefix import prefix_command

@prefix_command(name="ping")
async def ping(ctx: sosad.PrefixContext) -> None:
    await ctx.send("Pong!")
```

Or via the Client:

```python
bot = sosad.Client(token="...", intents=...)
bot.prefix = "!"

@bot.prefix_command(name="echo")
async def echo(ctx: sosad.PrefixContext, *, text: str) -> None:
    await ctx.send(text)
```

## Command Groups

```python
from sosad import command_group

group = command_group("math", "Math operations")

@group.sub_command("add", "Add two numbers")
async def add(
    ctx: sosad.InteractionContext,
    a: int = sosad.annotations.Integer(description="First number"),
    b: int = sosad.annotations.Integer(description="Second number"),
) -> None:
    await ctx.respond(f"{a} + {b} = {a + b}")
```

## Context Methods

The `InteractionContext` provides:

```python
await ctx.respond("Hello!")              # Initial response
await ctx.respond().content("Hi!").send() # Builder pattern
await ctx.edit("Updated!")                # Edit response
await ctx.delete()                        # Delete response
await ctx.defer()                         # Defer (thinking...)
await ctx.followup("Extra!")              # Follow-up message
```

## discord.py Compat

```python
import sosad.compat as discord

bot = discord.Bot(command_prefix="!", intents=..., token="...")

@bot.command(name="ping")   # Slash command via compat
async def ping(ctx):
    await ctx.send("Pong!")

@bot.prefix_command(name="echo")  # Prefix command
async def echo(ctx, *, text: str):
    await ctx.send(text)
```
