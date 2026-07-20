# Migration from discord.py

## The 1-Line Migration

```python
# BEFORE
import discord

# AFTER
import sosad.compat as discord
```

That's it. Your existing code works.

## What changes automatically

| Feature | discord.py | SoSad (automatic) |
|---|---|---|
| Rate limiting | Manual | Per-route auto |
| Error handling | try/except | Pipeline |
| Logging | Basic | Structured |
| Type hints | Partial | Full strict |
| Memory leaks | Common | Managed |

## Full migration example

### Before (discord.py)

```python
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run("TOKEN")
```

### After (SoSad)

```python
import sosad.compat as discord

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run("TOKEN")
```

### What you get for free

- `await ctx.send()` now has automatic rate limit handling
- Errors are caught by the error pipeline instead of crashing
- All events are type-checked
- Structured logging is enabled

## Gradual migration

You don't have to migrate everything at once. Mix discord.py patterns with SoSad:

```python
import sosad.compat as discord

bot = discord.Bot(...)

# discord.py-style commands work
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

# SoSad-native commands also work
@sosad.slash_command("hello", "Say hello")
async def hello(ctx: sosad.InteractionContext):
    await ctx.respond("Hello!")

bot.run("TOKEN")
```

## Migration checklist

- [ ] Change `import discord` to `import sosad.compat as discord`
- [ ] Add `name=` to `@bot.command()` decorators
- [ ] Update `bot.run("TOKEN")` to read from config
- [ ] Test all commands
- [ ] (Optional) Gradually convert to SoSad-native API
