# Middleware

SoSad uses ASGI-style pipeline middleware. Every interaction passes through a chain of middleware before reaching the handler.

## How it works

```
Request arrives
    ↓
logging_middleware
    ↓ (calls next)
permission_check_middleware
    ↓ (calls next)
command_handler()
```

## Writing middleware

```python
async def my_middleware(ctx, next, scope):
    # BEFORE handler
    print(f"Before: {ctx.interaction.command_name}")

    await next(ctx, scope)  # call next middleware or handler

    # AFTER handler
    print(f"After: {ctx.interaction.command_name}")
```

## Registering middleware

```python
bot.use(my_middleware)
```

## Middleware can

### Run before/after

```python
async def timing(ctx, next, scope):
    import time
    start = time.monotonic()
    await next(ctx, scope)
    elapsed = (time.monotonic() - start) * 1000
    print(f"{ctx.interaction.command_name}: {elapsed:.1f}ms")
```

### Short-circuit (skip handler)

```python
async def auth(ctx, next, scope):
    if not is_authorized(ctx.author.id):
        await ctx.respond("Unauthorized").ephemeral()
        return  # don't call next
    await next(ctx, scope)
```

### Modify scope (add DI values)

```python
async def db_middleware(ctx, next, scope):
    db = await get_db_connection()
    scope.set(Database, db)  # available to handler via DI
    await next(ctx, scope)
```

### Catch errors

```python
async def error_catcher(ctx, next, scope):
    try:
        await next(ctx, scope)
    except Exception as e:
        await ctx.respond(f"Error: {e}").ephemeral()
```

## Built-in middleware

### Logging

```python
from sosad.middleware.builtins import logging_middleware
bot.use(logging_middleware)
```

## Middleware order

Middleware runs in the order you register it:

```python
bot.use(logging)      # runs first
bot.use(auth)         # runs second
bot.use(rate_limit)   # runs third
```

## Error handling middleware

The error pipeline is automatically added as middleware. You don't need to write error-catching middleware unless you want custom behavior.
