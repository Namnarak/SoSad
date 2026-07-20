# Middleware

SoSad's middleware system is inspired by ASGI — each command passes through a pipeline of middleware before reaching your handler.

## Why middleware?

- **Logging** — automatically log every command
- **Metrics** — track timing, error rates, usage
- **Permissions** — gate commands by role/permission
- **Cooldowns** — per-user or per-channel rate limits
- **Tracing** — OpenTelemetry integration

## Built-in middleware

### Logging

```python
import sosad

bot = sosad.Client(token="...", intents=...)
bot.use(sosad.middleware.logging_middleware)
```

### Metrics

```python
bot.use(sosad.middleware.request_metrics)

# Later:
from sosad.middleware import get_metrics
metrics = get_metrics()
print(metrics["total_requests"])    # 42
print(metrics["command_timings"])   # {"ping": [0.023, 0.019]}
```

## Custom middleware

```python
from sosad.context import InteractionContext
from sosad.di.scopes import ScopeManager
from sosad.middleware.types import HandlerFunc

async def my_middleware(
    ctx: InteractionContext,
    next_fn: HandlerFunc,
    scope: ScopeManager,
) -> None:
    print(f"Before: {ctx.interaction.command_name}")
    await next_fn(ctx, scope)
    print(f"After: {ctx.interaction.command_name}")

bot.use(my_middleware)
```

### With DI access

```python
async def db_middleware(
    ctx: InteractionContext,
    next_fn: HandlerFunc,
    scope: ScopeManager,
) -> None:
    # Provide a DB session via DI
    async with get_session() as session:
        scope.set("db", session)
        await next_fn(ctx, scope)
```

## Middleware stack order

Middleware runs in registration order:

```
Request → middleware_1 → middleware_2 → ... → handler → ... → middleware_2 → middleware_1 → Response
```

## Error handling in middleware

```python
async def error_handling_middleware(
    ctx: InteractionContext,
    next_fn: HandlerFunc,
    scope: ScopeManager,
) -> None:
    try:
        await next_fn(ctx, scope)
    except Exception as e:
        await ctx.respond(f"Error: {e}")
        # Don't re-raise — error is handled
```

## Skip middleware for specific commands

```python
from sosad.middleware.types import MiddlewareFunc

def skip_logging(command_name: str) -> MiddlewareFunc:
    """Returns middleware that skips logging for specific commands."""
    async def middleware(ctx, next_fn, scope):
        if ctx.interaction.command_name != command_name:
            print(f"Executing: {command_name}")
        await next_fn(ctx, scope)
    return middleware
```
