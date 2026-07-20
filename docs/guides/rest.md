# REST API Client

REST mode runs without a Gateway connection. Perfect for:

- Discord webhooks (GitHub, Stripe, etc.)
- Serverless (Cloudflare Workers, AWS Lambda)
- Microservices
- Read-only bots

## Usage

```python
from sosad import RESTClient

bot = RESTClient(
    token="YOUR_TOKEN",
    public_key="YOUR_PUBLIC_KEY",
)

async def handle_webhook(request):
    return await bot.handle_request(request)
```

## Route registration

```python
# In a plugin
@sosad.slash_command("stats", "Bot stats")
async def stats(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Bot is running in REST mode!")
```

## Why REST mode?

| Feature | Gateway | REST mode |
|---|---|---|
| Connection | Persistent WebSocket | HTTP requests |
| Latency | Real-time | Request-response |
| Scalability | Sharded | Stateless (easy scale) |
| Serverless | ❌ | ✅ |
| Cold start | ❌ | ✅ (fast) |
| Resource usage | High (always-on) | Low (per-request) |
| Webhook support | ❌ | ✅ |

## Deployment

### Cloudflare Workers

```python
from sosad import RESTClient

bot = RESTClient(token=..., public_key=...)

async def fetch(request):
    return await bot.handle_request(request)
```

### AWS Lambda

```python
from sosad import RESTClient

bot = RESTClient(token=..., public_key=...)

def handler(event, context):
    return await bot.handle_request(event)
```
