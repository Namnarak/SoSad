# Dependency Injection

SoSad has a built-in FastAPI-style DI container. No need for `global` variables or manual wiring.

## Basic usage

```python
from sosad import inject
from sosad.di import Container

container = Container()

# Register a service
class Database:
    async def query(self, sql: str) -> list[dict]:
        ...

container.register(Database, instance=Database())

# Inject into a command
@sosad.slash_command("users", "List users")
async def list_users(
    ctx: sosad.InteractionContext,
    db: Database = inject(Database),
) -> None:
    users = await db.query("SELECT * FROM users")
    await ctx.respond(f"Found {len(users)} users")
```

## Providers

### Singleton

```python
container.register(Database, singleton=True)  # One instance for lifetime
```

### Scoped

```python
container.register(RequestContext, scoped=True)  # New instance per request
```

### Factory

```python
def create_db():
    return Database(url="sqlite:///bot.db")

container.register_factory(Database, create_db)
```

## Auto-wiring

SoSad can auto-resolve dependencies based on type annotations:

```python
@sosad.slash_command("stats", "Bot stats")
async def stats(
    ctx: sosad.InteractionContext,
    db: Database,            # Auto-resolved from container
    config: BotConfig,       # Auto-resolved from container
) -> None:
    ...
```

## Scope manager

The `ScopeManager` is available in middleware and events:

```python
async def my_middleware(ctx, next_fn, scope: ScopeManager):
    # Set scoped values
    scope.set("request_id", str(uuid4()))
    scope.set("db", db_session())

    await next_fn(ctx, scope)
```

## Sharing across middlewares and commands

```python
# middleware_a.py
async def set_timing(ctx, next_fn, scope):
    scope.set("start_time", time.time())
    await next_fn(ctx, scope)

# middleware_b.py
async def log_timing(ctx, next_fn, scope):
    await next_fn(ctx, scope)
    start = scope.get("start_time")
    print(f"Took {time.time() - start:.2f}s")
```

## Container hierarchy

```
Global Container
  └── Plugin Container (per-plugin overrides)
        └── Request Scope (per-command instances)
```
