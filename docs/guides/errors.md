# Error Handling

SoSad has a pipeline-based error handling system. Errors propagate through middleware and can be caught globally.

## Global error handler

```python
import sosad

bot = sosad.Client(token="...", intents=...)

@bot.on_error
async def handle_error(ctx: sosad.InteractionContext, error: Exception) -> None:
    if isinstance(error, sosad.CommandNotFound):
        await ctx.respond("Command not found!")
    elif isinstance(error, sosad.CheckFailed):
        await ctx.respond("You don't have permission!")
    else:
        await ctx.respond(f"Error: {error}")
        logger.exception("Unhandled error")
```

## Error types

| Error | Raised when |
|---|---|
| `CommandNotFound` | Unknown command |
| `CommandError` | Command execution failed |
| `CheckFailed` | Check returned False |
| `RateLimited` | Rate limit hit |
| `SoSadError` | Base error |

## In middleware

```python
async def error_middleware(ctx, next_fn, scope):
    try:
        await next_fn(ctx, scope)
    except sosad.CommandNotFound:
        await ctx.respond("Unknown command!")
    except sosad.CheckFailed:
        await ctx.respond("Permission denied!")
    except Exception as e:
        await ctx.respond(f"Something went wrong: {e}")
        raise  # Re-raise for global handler

bot.use(error_middleware)
```

## discord.py compat

```python
bot = discord.Bot(command_prefix="!", intents=..., token="...")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {error}")
```
