# Context

## InteractionContext

The context object passed to every command handler.

```python
@sosad.slash_command("info", "User info")
async def info(ctx: sosad.InteractionContext) -> None:
    # Basic properties
    ctx.author       # hikari.User
    ctx.channel_id   # int
    ctx.guild_id     # int | None
    ctx.interaction  # hikari.CommandInteraction

    # Respond
    await ctx.respond("Hello!")                 # Simple
    await ctx.respond().content("Hi!").send()   # Builder
    await ctx.respond(embed=embed)              # With embed

    # Edit / delete
    await ctx.edit("Updated!")
    await ctx.delete()

    # Defer (for long operations)
    await ctx.defer()
    # ... do work ...
    await ctx.edit("Done!")

    # Follow-up
    await ctx.followup("Extra message!")
```

## ResponseBuilder

The builder pattern for complex responses:

```python
await ctx.respond() \
    .content("Hello!") \
    .embed(embed) \
    .set_components(view) \
    .ephemeral() \
    .send()
```

## PrefixContext

For prefix commands:

```python
@prefix_command(name="ping")
async def ping(ctx: sosad.PrefixContext) -> None:
    await ctx.send("Pong!")
    await ctx.reply("Replied to your message!")
```

## ComponentContext

For component interactions (buttons, selects, modals):

```python
@sosad.components.button("my_button")
async def on_button(ctx: sosad.ComponentContext) -> None:
    ctx.custom_id    # "my_button"
    ctx.values       # List of selected values (for selects)
    ctx.message      # The original message
    await ctx.respond("Clicked!")
```

## discord.py compat

```python
bot = discord.Bot(command_prefix="!", intents=..., token="...")

@bot.command(name="info")
async def info(ctx):
    await ctx.send("Hello!")       # Send message
    await ctx.reply("Reply!")      # Reply to message
    await ctx.edit("Edited!")      # Edit response
    await ctx.delete()             # Delete response
```
