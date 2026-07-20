# Client

## Gateway Client

```python
import hikari
import sosad

bot = sosad.Client(
    token="YOUR_TOKEN",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)

# Optional config
bot.prefix = "!"  # Prefix for text commands

bot.run()
```

## REST Client

```python
from sosad import RESTClient

bot = RESTClient(
    token="YOUR_TOKEN",
    public_key="YOUR_PUBLIC_KEY",
)

# For web frameworks (FastAPI, Quart, etc.)
app = FastAPI()
@app.post("/interactions")
async def interactions(request: Request):
    return await bot.handle_request(request)
```

## Client methods

```python
# Middleware
bot.use(sosad.middleware.logging_middleware)
bot.use(sosad.middleware.request_metrics)

# Error handling
@bot.on_error
async def on_error(ctx, error):
    await ctx.respond(str(error))

# Events
@bot.listen(hikari.GuildMessageCreateEvent)
async def on_message(event):
    print(f"Message: {event.content}")

# Tasks
@bot.task(hours=1)
async def clean_cache():
    cache.clear()
```

## Discord.py compat Bot

```python
import sosad.compat as discord
import hikari

bot = discord.Bot(
    command_prefix="!",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
    token="YOUR_TOKEN",
)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

bot.run()
```

## Auto-sharding

```python
import hikari
import sosad

bot = sosad.Client(
    token="YOUR_TOKEN",
    intents=hikari.Intents.ALL_UNPRIVILEGED,
    shards=hikari.ShardBucket(0, 10),  # 10 shards
)

# Or auto-shard based on guild count
bot.run()
```

## Graceful shutdown

```python
import signal

bot = sosad.Client(token="...", intents=...)

async def shutdown():
    await bot.close()

signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown()))
bot.run()
```
