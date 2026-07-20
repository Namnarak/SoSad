# Client

The Client is the main entry point for SoSad. It wraps Hikari's GatewayBot.

## Basic usage

```python
import hikari
import sosad

bot = sosad.Client(
    token="YOUR_TOKEN",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)

bot.run()
```

## With config

```python
class Config(sosad.Settings):
    token: str
    debug: bool = False

config = Config()
bot = sosad.Client(
    token=config.token,
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)
```

## Using `app` alias

```python
# These are equivalent
bot = sosad.Client(...)
app = sosad.Client(...)
```

## Properties

| Property | Type | Description |
|---|---|---|
| `bot` | `hikari.GatewayBot` | The underlying Hikari bot |
| `rest` | `hikari.api.RESTProvider` | REST API client |
| `app` | `App` | Application state container |
| `container` | `Container` | DI container |
| `error_pipeline` | `ErrorPipeline` | Error handler pipeline |

## Client options

```python
bot = sosad.Client(
    token="TOKEN",                          # required
    intents=hikari.Intents.ALL_UNPRIVILEGED, # required
    logs="INFO",                             # logging level
    banner="so sad",                         # startup banner
    auto_discover_plugins=True,              # auto-discover plugins/
)
```

## Middleware

```python
async def logging_middleware(ctx, next, scope):
    import time
    start = time.monotonic()
    await next(ctx, scope)
    elapsed = (time.monotonic() - start) * 1000
    print(f"{ctx.interaction.command_name}: {elapsed:.1f}ms")

bot.use(logging_middleware)
```

## Error handling

```python
@bot.on_error(sosad.CheckFailed)
async def handle_check(error, ctx):
    await ctx.respond(str(error)).ephemeral()

@bot.on_error(Exception)
async def handle_any(error, ctx):
    await ctx.respond("Something went wrong").ephemeral()
```

## Loading plugins

```python
# Auto-discover from plugins/ (default)
bot = sosad.Client(..., auto_discover_plugins=True)

# Manual load
bot.load_plugins("plugins/", "extra_plugins/")
```
