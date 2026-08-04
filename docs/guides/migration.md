# Migration from discord.py

## Drop-in import

```python
# BEFORE
import discord

# AFTER (install SoSad and keep the original import)
import discord
```

SoSad's wheel provides the top-level `discord` shim, including
`discord.ext.commands`, `discord.ext.tasks`, `discord.ui`, and
`discord.app_commands`. `import sosad.compat as discord` remains available as
an explicit alternative.

## Full example

=== "Before (discord.py)"

    ```python
    import discord
    from discord.ext import commands

    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

    @bot.command()
    async def ping(ctx):
        await ctx.send("Pong!")

    bot.run("TOKEN")
    ```

=== "After (SoSad)"

    ```python
    import discord
    from discord.ext import commands

    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

    @bot.command(name="ping")
    async def ping(ctx):
        await ctx.send("Pong!")

    bot.run("TOKEN")
    ```

## What changes

| discord.py | SoSad compat | Notes |
|---|---|---|
| `discord.Embed` | `discord.Embed` | Same API, `inline=True` default |
| `discord.Colour` | `discord.Colour` | Same API |
| `discord.File` | `discord.File` | Re-exported from hikari |
| `discord.Intents.default()` | `discord.Intents.default()` | Returns `hikari.Intents.ALL_UNPRIVILEGED` |
| `@bot.command()` | `@bot.command()` | Prefix-compatible command |
| `@bot.hybrid_command()` | `@bot.hybrid_command()` | Registers a SoSad slash command |
| `@bot.event` | `@bot.event` | Common gateway events are adapted |
| `bot.run("TOKEN")` | `bot.run("TOKEN")` | Token may also be passed to `Bot(...)` |

## What you get for free

- **Automatic rate limiting** — no more `on_request_limit` handlers
- **Error pipeline** — global error handling with `@bot.on_error`
- **Structured logging** — JSON-ready logging
- **Type safety** — pyright strict
- **Plugin auto-discovery** — drop files in `plugins/`
- **Background tasks** — `@bot.task(hours=1)` decorator
- **Middleware** — before/after hooks for every command

## API compatibility matrix

| API | discord.py | SoSad compat |
|---|---|---|
| `Embed(title=, description=)` | ✅ | ✅ |
| `Embed.add_field(name=, value=)` | ✅ | ✅ |
| `Embed.set_image(url=)` | ✅ | ✅ |
| `Embed.set_footer(text=)` | ✅ | ✅ |
| `Colour.green()` | ✅ | ✅ |
| `Object(id=)` | ✅ | ✅ |
| `Webhook.from_url(url=)` | ✅ | ✅ |
| `utils.get()` | ✅ | ✅ |
| `utils.utcnow()` | ✅ | ✅ |
| `app_commands.command()` | ✅ | ✅ |
| `app_commands.describe()` | ✅ | ✅ |
| `app_commands.choices()` | ✅ | ✅ |
| `Intents.default()` | ✅ | Returns `hikari.Intents.ALL_UNPRIVILEGED` |

## Checklist

- [ ] Install `sosad` and keep `import discord`
- [ ] Or change to `import sosad.compat as discord`
- [ ] Add `import hikari` only when using Hikari-specific APIs
- [ ] Add `name=` where a command's name differs from its function name
- [ ] Test all commands
- [ ] (Optional) Migrate to SoSad-native API for full benefits
