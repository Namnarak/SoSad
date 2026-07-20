# Dependency Injection

SoSad has FastAPI-style auto-resolution. No `inject()` marker needed.

## How it works

```python
class Database:
    def __init__(self):
        self.connected = True

bot.container.singleton(Database)

@sosad.slash_command("check", "Check DB")
async def check_db(ctx, db: Database):
    # db is auto-resolved from container
    print(db.connected)  # True
```

## Registration types

### Singleton (created once)

```python
bot.container.singleton(Database)

# Or as decorator
@bot.container.singleton
class Database:
    ...
```

### Factory (created per-request)

```python
@bot.container.factory
class HttpClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()
```

### Value (pre-built instance)

```python
config = load_config()
bot.container.value(Config, config)
```

## Resolution order

1. Scoped values (from middleware)
2. Pre-built values
3. Singletons (cached)
4. Factories (new each time)
5. Direct instantiation

## Scoped dependencies

Middleware can add scoped values:

```python
async def db_middleware(ctx, next, scope):
    db = await create_connection()
    scope.set(Database, db)  # per-request
    await next(ctx, scope)
    await db.close()  # cleanup
```

## Auto-detection

Any parameter with a non-primitive type annotation is auto-resolved:

```python
# Primitive types → from interaction options
async def hello(ctx, name: str, count: int):
    ...

# Complex types → from DI container
async def ban(ctx, user: hikari.User, db: Database, cache: Cache):
    ...
```

## Container hierarchy

```python
# Global container
bot.container.singleton(Database)

# Per-request scope (in middleware)
scope.set(RequestId, generate_id())

# Handler receives both
async def handler(ctx, db: Database, req_id: RequestId):
    ...
```
