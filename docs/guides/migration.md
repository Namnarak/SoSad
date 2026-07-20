# Migration from discord.py

## The 1-line change

```python
# BEFORE
import discord

# AFTER
import sosad.compat as discord
```

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
    import sosad.compat as discord
    import hikari

    bot = discord.Bot(
        command_prefix="!",
        intents=hikari.Intents.ALL_UNPRIVILEGED,
        token="TOKEN",
    )

    @bot.prefix_command(name="ping")
    async def ping(ctx):
        await ctx.send("Pong!")

    bot.run()
    ```

## What changes

| discord.py | SoSad compat | Notes |
|---|---|---|
| `discord.Embed` | `discord.Embed` | Same API, `inline=True` default |
| `discord.Colour` | `discord.Colour` | Same API |
| `discord.File` | `discord.File` | Re-exported from hikari |
| `discord.Intents.default()` | `hikari.Intents.ALL_UNPRIVILEGED` | Different intents model |
| `@bot.command()` | `@bot.prefix_command()` | Must use `name=` |
| `@bot.slash_command()` | `@bot.command()` | discord.py compat name |
| `@bot.event` | `@bot.listen()` | Different event system |
| `bot.run("TOKEN")` | `bot.run("TOKEN")` | Same |

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
| `Intents.default()` | ❌ | Use `hikari.Intents.ALL_UNPRIVILEGED` |

## Checklist

- [ ] Change `import discord` to `import sosad.compat as discord`
- [ ] Add `import hikari` for intents
- [ ] Change `discord.Intents.default()` to `hikari.Intents.ALL_UNPRIVILEGED`
- [ ] Add `name=` to `@bot.command()` → `@bot.prefix_command(name=...)`
- [ ] Test all commands
- [ ] (Optional) Migrate to SoSad-native API for full benefits
