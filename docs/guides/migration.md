# Migration from discord.py

## The 1-line change

```python
# BEFORE
import discord

# AFTER
import sosad.compat as discord
```

## Example

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

    bot = discord.Bot(intents=discord.Intents.default())

    @bot.command(name="ping")
    async def ping(ctx):
        await ctx.send("Pong!")

    bot.run("TOKEN")
    ```

## What you get for free

- [x] Automatic rate limiting
- [x] Error pipeline
- [x] Structured logging
- [x] Type safety
- [x] Plugin auto-discovery

## Checklist

- [ ] Change `import discord` to `import sosad.compat as discord`
- [ ] Add `name=` to `@bot.command()` decorators
- [ ] Test all commands
- [ ] (Optional) Migrate to SoSad-native API
