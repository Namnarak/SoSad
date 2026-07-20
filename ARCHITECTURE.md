# SoSad Discord Framework — Architecture

> A decorator-first, pipeline-middleware Discord framework built on Hikari.
> Python 3.13+ · asyncio · Pydantic v2 · Ruff + Pyright strict

---

## 1. Package Structure

```
sosad/
├── __init__.py                 # Public API re-exports: Client, slash_command, listen, etc.
├── _meta.py                    # Version, package metadata
│
├── core/
│   ├── __init__.py
│   ├── client.py               # SoSad client wrapping hikari.GatewayBot
│   ├── app.py                  # Application state container (lifespan, shared objects)
│   └── constants.py            # Sentinel values, internal enums
│
├── commands/
│   ├── __init__.py
│   ├── decorators.py           # @slash_command(), @sub_command(), @command_group()
│   ├── registration.py         # Collects decorator metadata → CommandRegistry
│   ├── registry.py             # In-memory command tree + diff logic
│   ├── sync.py                 # Syncs registry to Discord API
│   ├── router.py               # Routes InteractionCreateEvent → correct handler
│   └── models.py               # CommandMeta, OptionDescriptor, SubCommandMeta
│
├── context/
│   ├── __init__.py
│   └── context.py              # InteractionContext (immutable) + ResponseBuilder
│
├── events/
│   ├── __init__.py
│   ├── typed.py                # @listen[E]() generic decorator
│   ├── dispatcher.py           # Wraps hikari event dispatch with type-safe routing
│   └── models.py               # EventListenerMeta
│
├── middleware/
│   ├── __init__.py
│   ├── types.py                # Middleware protocol + ChainRunner
│   ├── builtins.py             # logging, defer, permission-check middleware
│   └── registry.py             # Middleware stack builder
│
├── di/
│   ├── __init__.py
│   ├── container.py            # DI container: register, resolve, scoping
│   ├── providers.py            # factory(), singleton(), value()
│   ├── scopes.py               # Scope enum + ScopeManager
│   └── markers.py              # inject() sentinel + Annotated helpers
│
├── plugins/
│   ├── __init__.py
│   ├── loader.py               # Module discovery, import, lifecycle
│   ├── manager.py              # PluginManager: load/unload/reload
│   └── base.py                 # Plugin protocol / base class (optional)
│
├── errors/
│   ├── __init__.py
│   ├── base.py                 # SoSadError hierarchy
│   ├── handler.py              # ErrorPipeline: catch → transform → respond
│   └── builtin.py              # CommandNotFound, CheckFailed, RateLimited, etc.
│
├── cooldowns/
│   ├── __init__.py
│   ├── buckets.py              # BucketScope: user, guild, channel, member, role
│   ├── storage.py              # CooldownStorage protocol + InMemoryStorage
│   └── decorator.py            # @cooldown() decorator
│
├── checks/
│   ├── __init__.py
│   ├── base.py                 # Check protocol + CheckResult
│   ├── builtin.py              # is_owner, has_role, in_guild, dm_only, etc.
│   └── decorator.py            # @check() decorator
│
├── permissions/
│   ├── __init__.py
│   ├── resolver.py             # Permission bitfield resolution
│   ├── decorator.py            # @requires_permissions() decorator
│   └── builtin.py              # Common permission presets
│
├── utils/
│   ├── __init__.py
│   ├── typing.py               # Type alias helpers, TypeVar utilities
│   ├── importing.py            # Dynamic module import with error handling
│   └── async_utils.py          # TaskGroup wrappers, timeout helpers
│
└── cli/                        # Optional CLI entry point
    ├── __init__.py
    └── runner.py               # `python -m sosad` entry point
```

---

## 2. Module Responsibilities & Public APIs

### 2.1 `core/client.py` — The Client

**Responsibility**: Single entry point. Owns the Hikari GatewayBot. Drives the lifecycle (setup → run → teardown).

```python
class Client:
    """The main SoSad client. Wraps hikari.GatewayBot."""

    def __init__(
        self,
        *,
        token: str,
        intents: hikari.Intents,
        # Hikari GatewayBot kwargs forwarded (cache_settings, etc.)
        logs: str | int = "INFO",
        banner: str = "so sad",
    ) -> None: ...

    # --- Public API ---
    def slash_command(
        self,
        name: str,
        description: str,
        *,
        scopes: Sequence[hikari.Snowflake | Literal["guild", "global"]] = ("global",),
        default_member_permissions: hikari.Permissions | None = None,
        is_dm_only: bool = False,
    ) -> Callable[..., SlashCommandMeta]: ...

    def listen(self, event_type: type[E]) -> Callable[..., EventListenerMeta]: ...

    def use(self, *middlewares: MiddlewareFunc) -> None:
        """Register global middleware (applied to all interactions)."""

    def add_check(self, check: CheckFunc) -> None:
        """Register global check (applied to all commands)."""

    def on_error(self, error_type: type[Exception]) -> Callable[..., None]:
        """Register error handler for specific exception types."""

    def load_plugins(self, *paths: str | Path) -> None:
        """Discover and load plugin modules."""

    async def start(self) -> None:
        """Run setup (DI, plugin load, command sync) then start gateway."""

    async def close(self) -> None:
        """Graceful shutdown."""
```

**Key design decision**: `Client` is the composition root. It does NOT subclass `GatewayBot`. It owns one via composition. This keeps Hikari as a dependency, not a base class.

**Tradeoff** — Composition over inheritance: More verbose forwarding, but the client API stays clean and Hikari internals never leak into SoSad's type signatures.

### 2.2 `context/context.py` — Immutable Context

**Responsibility**: Wraps a `CommandInteraction` into a convenient, immutable context object. Responses are built via a builder pattern.

```python
@dataclass(frozen=True, slots=True)
class InteractionContext:
    """Immutable snapshot of an interaction. Created once per request."""

    # Read-only fields (all frozen)
    interaction: hikari.CommandInteraction
    client: Client
    app: App

    # --- Convenience properties ---
    @property
    def author(self) -> hikari.User: ...

    @property
    def guild_id(self) -> hikari.Snowflake | None: ...

    @property
    def channel_id(self) -> hikari.Snowflake: ...

    @property
    def options(self) -> dict[str, hikari.CommandInteractionOption]: ...

    def get_option(self, name: str, default: T = _MISSING) -> T: ...

    def get_str(self, name: str) -> str: ...
    def get_int(self, name: str) -> int: ...
    def get_user(self, name: str) -> hikari.User: ...
    def get_channel(self, name: str) -> hikari.GuildChannel: ...
    def get_role(self, name: str) -> hikari.Role: ...

    # --- Response builder (returns new builder, never mutates) ---
    def respond(self) -> ResponseBuilder: ...

    def edit_response(self) -> ResponseBuilder: ...

    # --- DI access ---
    def resolve(self, annotation: type[T]) -> T:
        """Resolve a dependency from the scoped container."""
        ...


@dataclass(frozen=True, slots=True)
class ResponseBuilder:
    """Immutable builder for interaction responses. Each method returns a new builder."""

    _interaction: hikari.CommandInteraction
    _response_type: hikari.ResponseType
    _content: str | None
    _embeds: tuple[hikari.Embed, ...]
    _components: tuple[hikari.ComponentBuilder, ...]  # future
    _flags: hikari.MessageFlag
    _files: tuple[hikari.File, ...]

    def content(self, text: str) -> ResponseBuilder: ...
    def embed(self, embed: hikari.Embed) -> ResponseBuilder: ...
    def embeds(self, *embeds: hikari.Embed) -> ResponseBuilder: ...
    def file(self, file: hikari.File) -> ResponseBuilder: ...
    def files(self, *files: hikari.File) -> ResponseBuilder: ...
    def flag(self, flag: hikari.MessageFlag) -> ResponseBuilder: ...
    def ephemeral(self) -> ResponseBuilder: ...
    def components(self, *components: hikari.ComponentBuilder) -> ResponseBuilder: ...

    async def send(self) -> hikari.MessageResponse:
        """Execute the response."""
        ...

    async def defer(self, *, ephemeral: bool = False) -> None:
        """Defer the interaction response."""
        ...
```

**Key design decision**: Every `ResponseBuilder` method returns a **new** `ResponseBuilder` (frozen dataclass). The original is never mutated.

**Tradeoff** — Immutability vs performance: Creating new builder instances per method call adds allocation pressure, but it eliminates an entire class of bugs (shared mutable state, accidental reuse). For a Discord bot, this cost is negligible compared to network latency.

### 2.3 `middleware/` — Pipeline Middleware

**Responsibility**: ASGI-style middleware pipeline that wraps every interaction. Middleware can run logic before/after the handler, short-circuit, or modify the context.

```python
# --- types.py ---

class MiddlewareFunc(Protocol):
    """A middleware function. Receives context, next handler, and DI scope."""
    async def __call__(
        self,
        ctx: InteractionContext,
        next: HandlerFunc,
        scope: ScopeManager,
    ) -> None: ...

class HandlerFunc(Protocol):
    """The next step in the middleware chain (either next middleware or the actual handler)."""
    async def __call__(
        self,
        ctx: InteractionContext,
        scope: ScopeManager,
    ) -> None: ...

# --- registry.py ---

class MiddlewareStack:
    """Builds and runs the middleware pipeline."""

    def __init__(self) -> None:
        self._middlewares: list[MiddlewareFunc] = []

    def add(self, middleware: MiddlewareFunc) -> None:
        self._middlewares.append(middleware)

    def build(self) -> HandlerFunc:
        """Returns the composed handler. Last-added wraps first."""
        # Builds chain: m3 → m2 → m1 → handler
        handler: HandlerFunc = self._final_handler
        for mw in reversed(self._middlewares):
            handler = _wrap(mw, handler)
        return handler

# --- builtins.py ---

async def logging_middleware(ctx: InteractionContext, next: HandlerFunc, scope: ScopeManager) -> None:
    """Logs command invocation with timing."""
    start = time.monotonic()
    try:
        await next(ctx, scope)
    finally:
        elapsed = time.monotonic() - start
        logger.info("%s completed in %.2fms", ctx.interaction.command_name, elapsed * 1000)

async def defer_middleware(ctx: InteractionContext, next: HandlerFunc, scope: ScopeManager) -> None:
    """Auto-defer if handler takes > 2.5s (runs handler in background)."""
    task = asyncio.create_task(next(ctx, scope))
    done, _ = await asyncio.wait({task}, timeout=2.5)
    if not done:
        await ctx.respond().defer()
        await task
```

**How it works**:

```
Request arrives
    ↓
middleware_stack.build() → composed handler
    ↓
logging_middleware
    ↓ (calls next)
permission_check_middleware
    ↓ (calls next)
cooldown_middleware
    ↓ (calls next)
command_handler()
```

Each middleware receives:
1. `ctx` — the immutable interaction context
2. `next` — a callable that invokes the next layer
3. `scope` — the DI scope for this request (allows middleware to add scoped dependencies)

Middleware can:
- **Run before**: `await next(ctx, scope)` then do post-processing
- **Short-circuit**: Don't call `next`, respond directly
- **Modify scope**: Add scoped values before `next(ctx, scope)`
- **Catch errors**: Wrap `next` in try/except

**Key design decision**: Middleware is a flat list (not a tree). Each middleware wraps the next. This is simpler than a graph and covers all real use cases.

**Tradeoff** — Flat pipeline vs hook tree: A flat pipeline is easier to reason about, debug, and compose. Tree-based hook systems (like lightbulb's) allow parallel execution but add complexity. For Discord interactions (one handler per request), parallelism is unnecessary.

### 2.4 `commands/` — Command System

**Responsibility**: Decorator-based command registration, metadata collection, routing, and Discord sync.

#### `decorators.py` — The Public API

```python
def slash_command(
    name: str,
    description: str,
    *,
    scopes: Sequence[hikari.Snowflake | Literal["guild", "global"]] = ("global",),
    default_member_permissions: hikari.Permissions | None = None,
    is_dm_only: bool = False,
    nsfw: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., SlashCommandMeta]]:
    """Decorator that marks a function as a slash command.

    Usage:
        @sosad.slash_command("ping", "Check bot latency")
        async def ping(ctx: InteractionContext) -> None:
            await ctx.respond().content("Pong!").send()
    """
    ...

def sub_command(
    group: str,
    name: str,
    description: str,
    *,
    parent_scopes: Sequence[hikari.Snowflake | Literal["guild", "global"]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., SubCommandMeta]]:
    """Decorator for a subcommand within a group.

    Usage:
        @sosad.sub_command("config", "set", "Set a configuration value")
        async def config_set(ctx: InteractionContext, key: str, value: str) -> None:
            ...
    """
    ...

def command_group(
    name: str,
    description: str,
    *,
    scopes: Sequence[hikari.Snowflake | Literal["guild", "global"]] = ("global",),
    default_member_permissions: hikari.Permissions | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., CommandGroupMeta]]:
    """Decorator for a command group.

    Usage:
        @sosad.command_group("config", "Bot configuration commands")
        async def config(ctx: InteractionContext) -> None:
            pass  # group root (optional handler)
    """
    ...
```

#### `models.py` — Metadata Objects

```python
@dataclass(frozen=True, slots=True)
class OptionDescriptor:
    """Describes a single slash command option."""
    name: str
    description: str
    type: hikari.OptionType
    required: bool = True
    choices: Sequence[tuple[str, str | int | float]] | None = None
    autocomplete: bool = False

@dataclass(frozen=True, slots=True)
class SlashCommandMeta:
    """Metadata collected by @slash_command decorator."""
    name: str
    description: str
    handler: Callable[..., Any]
    options: tuple[OptionDescriptor, ...]
    scopes: tuple[hikari.Snowflake | Literal["guild", "global"], ...]
    default_member_permissions: hikari.Permissions | None
    is_dm_only: bool
    nsfw: bool
    checks: tuple[CheckFunc, ...]
    cooldown: CooldownConfig | None
    middleware: tuple[MiddlewareFunc, ...]

@dataclass(frozen=True, slots=True)
class SubCommandMeta:
    """Metadata collected by @sub_command decorator."""
    group: str
    name: str
    description: str
    handler: Callable[..., Any]
    options: tuple[OptionDescriptor, ...]
    parent_scopes: tuple[hikari.Snowflake | Literal["guild", "global"], ...] | None
    checks: tuple[CheckFunc, ...]
    cooldown: CooldownConfig | None

@dataclass(frozen=True, slots=True)
class CommandGroupMeta:
    """Metadata collected by @command_group decorator."""
    name: str
    description: str
    subcommands: tuple[SubCommandMeta, ...]  # populated during registration
    scopes: tuple[hikari.Snowflake | Literal["guild", "global"], ...]
    default_member_permissions: hikari.Permissions | None
```

#### `registration.py` — Metadata Collection

```python
# Global registry populated by decorators at import time
_registry: CommandRegistry = CommandRegistry()

def register_command(meta: SlashCommandMeta | CommandGroupMeta) -> None:
    """Called by decorators to add metadata to the registry."""
    _registry.add(meta)

def get_registry() -> CommandRegistry:
    return _registry
```

#### `registry.py` — Command Tree

```python
class CommandRegistry:
    """In-memory command tree. Supports diff for sync."""

    def __init__(self) -> None:
        self._commands: dict[str, SlashCommandMeta] = {}
        self._groups: dict[str, CommandGroupMeta] = {}

    def add(self, meta: SlashCommandMeta | CommandGroupMeta | SubCommandMeta) -> None: ...

    def build_hikari_commands(
        self,
    ) -> list[hikari.api.CommandBuilder]:
        """Convert internal metadata to Hikari command builders for API sync."""
        ...

    def diff(
        self,
        remote: list[hikari.InteractionCommand],
    ) -> CommandDiff:
        """Compare local registry with Discord's current commands."""
        ...

    def resolve(
        self,
        interaction: hikari.CommandInteraction,
    ) -> SlashCommandMeta | SubCommandMeta | None:
        """Given an interaction, find the correct handler."""
        ...
```

#### `router.py` — Interaction Routing

```python
class CommandRouter:
    """Routes InteractionCreateEvent to the correct handler through middleware."""

    def __init__(self, registry: CommandRegistry, stack: MiddlewareStack) -> None: ...

    async def handle_interaction(self, event: hikari.InteractionCreateEvent) -> None:
        """Entry point for all interaction events."""
        interaction = event.interaction
        if not isinstance(interaction, hikari.CommandInteraction):
            return  # not a command — future: component handling

        meta = self.registry.resolve(interaction)
        if meta is None:
            return  # unknown command, error handler catches this

        # Build context
        ctx = InteractionContext(
            interaction=interaction,
            client=self._client,
            app=self._app,
        )

        # Create scoped DI container
        scope = self._scope_manager.create_scope()
        scope.set(InteractionContext, ctx)

        # Run through middleware pipeline
        handler = self._stack.build()
        await handler(ctx, scope)
```

#### `sync.py` — Command Sync

```python
class CommandSyncer:
    """Syncs the local command registry to Discord."""

    def __init__(
        self,
        rest: hikari.api.RESTProvider,
        registry: CommandRegistry,
        app_id: hikari.Snowflake,
    ) -> None: ...

    async def sync(
        self,
        *,
        delete_orphans: bool = True,
    ) -> SyncResult:
        """
        1. Fetch current global + guild commands from Discord
        2. Diff against local registry
        3. Batch create/update/delete via REST API
        4. Return SyncResult with counts
        """
        ...

@dataclass(frozen=True)
class SyncResult:
    created: int
    updated: int
    deleted: int
    unchanged: int
    errors: list[SyncError]
```

**Sync Strategy**:
- Runs once at startup (before gateway connects)
- Full diff: fetch remote → compare with local → batch REST calls
- `delete_orphans=True` removes Discord commands not in local registry
- Guild commands synced per-guild (requires guild IDs in scopes)
- Errors are logged but don't block startup
- Future: `--sync-only` CLI flag for dry-run

### 2.5 `events/` — Typed Event System

**Responsibility**: Generic decorator for listening to Hikari events with type safety.

```python
# --- typed.py ---

def listen(event_type: type[E]) -> Callable[[Callable[[E], Awaitable[None]]], EventListenerMeta]:
    """Decorator for typed event listening.

    Usage:
        @sosad.listen(hikari.GuildMessageCreateEvent)
        async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
            print(event.message.content)
    """
    ...

# --- dispatcher.py ---

class EventDispatcher:
    """Wraps hikari's event dispatch with typed routing."""

    def __init__(self) -> None:
        self._listeners: dict[type[hikari.Event], list[EventListenerMeta]] = {}

    def register(self, meta: EventListenerMeta) -> None: ...

    def attach(self, bot: hikari.GatewayBot) -> None:
        """Hook into hikari's event system and route to typed listeners."""
        # For each registered event type:
        #   bot.listen(event_type)(self._dispatch)
        ...

    async def _dispatch(self, event: hikari.Event) -> None:
        """Route event to all matching listeners."""
        listeners = self._listeners.get(type(event), [])
        for listener in listeners:
            await listener.handler(event)
```

**Key design decision**: Events are plain Hikari event types with a generic decorator. No custom event system — we reuse Hikari's. The decorator just adds type safety and metadata collection.

**Tradeoff** — Reusing Hikari events vs custom events: Custom events would let us add Discord-specific abstractions (e.g., `MessageReceived` with parsed content). But it adds a translation layer and breaks compatibility with Hikari's ecosystem. For v1, reuse Hikari events directly.

### 2.6 `di/` — Dependency Injection

**Responsibility**: Type-hint-based dependency resolution with per-request scoping. Inspired by FastAPI's DI system.

```python
# --- container.py ---

class Container:
    """Global DI container. Holds singleton and factory registrations."""

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable[..., Any]] = {}
        self._values: dict[type, Any] = {}

    def singleton(self, cls: type[T]) -> type[T]:
        """Decorator: register a class as a singleton (created once)."""
        ...

    def factory(self, cls: type[T]) -> type[T]:
        """Decorator: register a class as a factory (created per-request)."""
        ...

    def value(self, cls: type[T], instance: T) -> None:
        """Register a pre-built instance."""
        ...

    async def resolve(
        self,
        annotation: type[T],
        scope: ScopeManager,
    ) -> T:
        """Resolve a dependency by type annotation."""
        # 1. Check scope (scoped values)
        # 2. Check singletons
        # 3. Check factories (create + cache in scope)
        # 4. Introspect __init__ annotations and recursively resolve
        ...

# --- scopes.py ---

class ScopeManager:
    """Per-request scoped dependency storage."""

    def __init__(self, parent: Container) -> None:
        self._scoped: dict[type, Any] = {}

    def set(self, cls: type[T], instance: T) -> None:
        """Set a scoped value (e.g., InteractionContext)."""
        ...

    async def resolve(self, annotation: type[T]) -> T | None:
        """Check if a scoped value exists for this type."""
        ...

    def cleanup(self) -> None:
        """Release scoped resources."""
        ...

# --- markers.py ---

T = TypeVar("T")

def inject(cls: T) -> T:
    """Marker for DI resolution in function parameters.

    Usage:
        @sosad.slash_command("ban", "Ban a user")
        async def ban(
            ctx: InteractionContext,
            user: hikari.User,
            reason: str,
            db: Database = inject(),  # resolved from DI container
        ) -> None:
            await db.log_ban(user.id, reason)
    """
    ...
```

**How DI integrates with commands**:

When a command handler is called, the router:
1. Creates a `ScopeManager` for the request
2. Stores `InteractionContext` in the scope
3. The middleware pipeline runs, adding more scoped values if needed
4. When the handler is called, its parameters are introspected:
   - Parameters with type annotations matching registered types → resolved from DI
   - Parameters named after option descriptors → extracted from interaction options
   - Parameters with `inject()` → force DI resolution
   - Plain parameters without annotations → treated as command options

```python
async def ban(
    ctx: InteractionContext,          # → resolved from scope (always available)
    user: hikari.User,                # → extracted from interaction option "user"
    reason: str,                      # → extracted from interaction option "reason"
    db: Database = inject(),          # → resolved from DI container
    audit_log: AuditLog = inject(),   # → resolved from DI container
) -> None:
    ...
```

**Resolution order**: Scope → Singletons → Factories → Recursive `__init__` introspection.

**Tradeoff** — Annotation-based DI vs explicit `Depends()`: Annotation-based is cleaner (no `Depends()` boilerplate) but requires careful parameter naming to avoid collisions with command options. The `inject()` marker disambiguates when needed.

### 2.7 `plugins/` — Plugin System

**Responsibility**: Module-based extension loading with lifecycle management.

```python
# --- base.py ---

class Plugin(Protocol):
    """Optional base protocol for plugins."""
    @staticmethod
    def setup(client: Client) -> None:
        """Called when the plugin is loaded. Register commands, events, etc."""
        ...

    @staticmethod
    async def on_load(client: Client) -> None:
        """Async initialization (DB connections, etc.)."""
        ...

    @staticmethod
    async def on_unload(client: Client) -> None:
        """Async cleanup."""
        ...

# --- loader.py ---

class PluginLoader:
    """Discovers and loads plugin modules."""

    @staticmethod
    def discover(
        *paths: str | Path,
        pattern: str = "*.py",
    ) -> list[Path]:
        """Find plugin modules by path/glob."""
        ...

    @staticmethod
    def load_module(path: Path) -> ModuleType:
        """Import a Python module from a file path."""
        ...

    @staticmethod
    def find_setup(module: ModuleType) -> Callable[[Client], None] | None:
        """Look for setup() function or Plugin protocol implementation."""
        ...

# --- manager.py ---

class PluginManager:
    """Manages plugin lifecycle."""

    def __init__(self, client: Client) -> None:
        self._client = client
        self._loaded: dict[str, LoadedPlugin] = {}

    async def load(self, path: Path) -> LoadedPlugin:
        """
        1. Import module
        2. Find setup() or Plugin impl
        3. Call setup(client) — registers commands/events
        4. Call on_load(client) if async init needed
        5. Track for hot-reload
        """
        ...

    async def unload(self, name: str) -> None:
        """Call on_unload(), deregister commands/events, remove from tracking."""
        ...

    async def reload(self, name: str) -> None:
        """unload() + load(). For hot-reload during development."""
        ...

    async def load_all(self, *paths: str | Path) -> None:
        """Discover and load all plugins from paths."""
        ...


@dataclass
class LoadedPlugin:
    name: str
    path: Path
    module: ModuleType
    commands: list[SlashCommandMeta | CommandGroupMeta]
    listeners: list[EventListenerMeta]
    loaded_at: datetime
```

**Plugin discovery flow**:
1. `client.load_plugins("plugins/")` → `PluginManager.load_all()`
2. `PluginLoader.discover("plugins/")` finds all `.py` files
3. Each module is imported via `importlib.util.spec_from_file_location()`
4. `setup(client)` is called — the plugin registers its commands/events via decorators
5. Decorators push metadata to the global `CommandRegistry` and `EventDispatcher`
6. On hot-reload: unload (deregister) → re-import module → re-register

**Key design decision**: Plugins register via `setup()` function (not class instantiation). This is simpler and avoids import-time side effects.

**Tradeoff** — Function-based vs class-based plugins: Function-based (`setup()`) is simpler but doesn't enforce structure. Class-based (`Plugin` protocol) adds structure but requires instantiation. The protocol is optional — users can use either style.

### 2.8 `errors/` — Error Handling

**Responsibility**: Pipeline-level error catching with typed exception hierarchy.

```python
# --- base.py ---

class SoSadError(Exception):
    """Base exception for all SoSad errors."""
    ...

class CommandError(SoSadError):
    """Error during command execution."""
    def __init__(self, message: str, *, ctx: InteractionContext | None = None): ...
    ...

class CheckFailed(CommandError):
    """A pre-condition check failed."""
    ...

class RateLimited(CommandError):
    """Cooldown exceeded."""
    def __init__(self, retry_after: float, *, ctx: InteractionContext | None = None): ...
    ...

class CommandNotFound(SoSadError):
    """No handler found for the interaction."""
    ...

class SyncError(SoSadError):
    """Error during command sync."""
    ...

# --- handler.py ---

class ErrorPipeline:
    """Collects error handlers and runs them in order."""

    def __init__(self) -> None:
        self._handlers: list[ErrorHandler] = []

    def on(
        self,
        error_type: type[E],
        handler: Callable[[E, InteractionContext], Awaitable[None]],
    ) -> None:
        """Register a handler for a specific exception type."""
        ...

    async def handle(
        self,
        error: Exception,
        ctx: InteractionContext | None = None,
    ) -> None:
        """
        Walk the handler chain:
        1. Find handlers matching the exception type (MRO order)
        2. Run the first matching handler
        3. If no handler matches, log + send generic error response
        """
        ...
```

**How errors flow**:

```
command_handler() raises CheckFailed
    ↓
Middleware catches via try/except around next()
    ↓
ErrorPipeline.handle(error, ctx)
    ↓
Registered handler for CheckFailed:
    → "You don't have permission to use this command."
    → ctx.respond().content(msg).ephemeral().send()
```

**Key design decision**: Errors bubble through the middleware pipeline. Any middleware can catch errors. Unhandled errors reach the `ErrorPipeline` at the top.

### 2.9 `cooldowns/` — Rate Limiting

**Responsibility**: Bucket-based cooldowns with multiple scopes.

```python
# --- buckets.py ---

class BucketScope(enum.Enum):
    USER = "user"
    GUILD = "guild"
    CHANNEL = "channel"
    MEMBER = "member"    # user + guild combined
    ROLE = "role"
    AUTHOR = "author"    # alias for USER (clarity)

@dataclass(frozen=True)
class CooldownConfig:
    rate: int                    # number of uses
    period: float                # time window in seconds
    bucket: BucketScope
    retry_after_message: str | None = None

# --- storage.py ---

class CooldownStorage(Protocol):
    async def acquire(self, key: str, config: CooldownConfig) -> CooldownResult: ...
    async def reset(self, key: str) -> None: ...

class InMemoryCooldownStorage:
    """In-memory cooldown storage using a dict with timestamps."""
    async def acquire(self, key: str, config: CooldownConfig) -> CooldownResult: ...

@dataclass(frozen=True)
class CooldownResult:
    allowed: bool
    remaining: int
    retry_after: float

# --- decorator.py ---

def cooldown(
    rate: int,
    period: float,
    bucket: BucketScope = BucketScope.USER,
    *,
    retry_after_message: str | None = None,
) -> Callable:
    """Decorator: apply cooldown to a command.

    Usage:
        @sosad.slash_command("work", "Earn coins")
        @sosad.cooldown(1, 60, bucket=BucketScope.USER)
        async def work(ctx: InteractionContext) -> None:
            ...
    """
    ...
```

**Cooldown key generation**: `"{command_name}:{bucket_value}"`. For `BucketScope.USER`: key is `"work:1234567890"` (user ID).

### 2.10 `checks/` — Pre-condition Validators

**Responsibility**: Decorator-based pre-condition checks that run before command handlers.

```python
# --- base.py ---

class CheckResult:
    """Result of a check evaluation."""
    def __init__(self, passed: bool, reason: str | None = None): ...

    @classmethod
    def ok(cls) -> CheckResult: ...
    @classmethod
    def fail(cls, reason: str) -> CheckResult: ...

class CheckFunc(Protocol):
    async def __call__(self, ctx: InteractionContext) -> CheckResult: ...

# --- decorator.py ---

def check(
    *checks: CheckFunc,
) -> Callable:
    """Decorator: apply checks to a command.

    Usage:
        @sosad.slash_command("ban", "Ban a user")
        @sosad.check(is_owner(), has_permissions(hikari.Permissions.BAN_MEMBERS))
        async def ban(ctx: InteractionContext) -> None:
            ...
    """
    ...

# --- builtin.py ---

def is_owner(*user_ids: hikari.Snowflake) -> CheckFunc: ...
def has_permissions(*perms: hikari.Permissions) -> CheckFunc: ...
def has_role(*role_ids: hikari.Snowflake) -> CheckFunc: ...
def in_guild() -> CheckFunc: ...
def dm_only() -> CheckFunc: ...
def guild_only() -> CheckFunc: ...
def bot_has_permissions(*perms: hikari.Permissions) -> CheckFunc: ...
```

**Check execution**: Checks run as middleware in the pipeline, before the handler. If any check fails, the pipeline short-circuits and raises `CheckFailed`.

### 2.11 `permissions/` — Permission Integration

**Responsibility**: Discord permission checking integrated with checks and command metadata.

```python
# --- resolver.py ---

class PermissionResolver:
    """Resolves permissions from interaction context."""

    @staticmethod
    def resolve_member_permissions(
        interaction: hikari.CommandInteraction,
    ) -> hikari.Permissions:
        """Get the member's effective permissions in the channel."""
        ...

    @staticmethod
    def has_permission(
        member_permissions: hikari.Permissions,
        required: hikari.Permissions,
    ) -> bool:
        ...

# --- decorator.py ---

def requires_permissions(*perms: hikari.Permissions) -> CheckFunc:
    """Check that the author has specific permissions.

    Usage:
        @sosad.slash_command("purge", "Delete messages")
        @sosad.requires_permissions(hikari.Permissions.MANAGE_MESSAGES)
        async def purge(ctx: InteractionContext) -> None:
            ...
    """
    ...
```

---

## 3. Middleware Pipeline — Full Architecture

### 3.1 Request Flow

```
Discord Gateway
    ↓
hikari.GatewayBot receives InteractionCreateEvent
    ↓
EventDispatcher routes to CommandRouter.handle_interaction()
    ↓
CommandRouter:
    1. Parse interaction → find handler in CommandRegistry
    2. Build InteractionContext (immutable)
    3. Create ScopeManager (DI scope)
    4. Store InteractionContext in scope
    5. Build middleware pipeline
    ↓
Middleware Pipeline (global middleware → command middleware → checks → cooldown → handler):
    ┌─ logging_middleware ─────────────────────────────┐
    │  ┌─ permission_middleware ──────────────────────┐ │
    │  │  ┌─ check_middleware ───────────────────────┐│ │
    │  │  │  ┌─ cooldown_middleware ────────────────┐││ │
    │  │  │  │  ┌─ command_handler() ─────────────┐│││ │
    │  │  │  │  │                                  ││││ │
    │  │  │  │  └──────────────────────────────────┘│││ │
    │  │  │  └───────────────────────────────────────┘││ │
    │  │  └────────────────────────────────────────────┘│ │
    │  └─────────────────────────────────────────────────┘ │
    └──────────────────────────────────────────────────────┘
    ↓
Response sent via Hikari REST API
    ↓
ScopeManager.cleanup() — release scoped resources
```

### 3.2 Middleware Application Order

1. **Global middleware** (registered via `client.use()`) — applies to all interactions
2. **Plugin middleware** (registered by plugins) — applies to all interactions from that plugin
3. **Command middleware** (registered via `@slash_command(middleware=...)`) — applies to specific commands
4. **Checks** (registered via `@check()`) — pre-condition validation
5. **Cooldowns** (registered via `@cooldown()`) — rate limiting
6. **Handler** — the actual command function

### 3.3 How Middleware Modifies Context

Middleware can't modify the immutable `InteractionContext`, but it can:
- Add scoped dependencies to `ScopeManager`: `scope.set(Database, db_connection)`
- Wrap the handler to catch/transform errors
- Short-circuit by not calling `next()` and responding directly
- Log, time, or instrument the request

---

## 4. DI Integration with Commands

### 4.1 Resolution Flow

When a command handler is called, the router introspects its signature:

```python
async def ban(
    ctx: InteractionContext,          # → from scope (always available)
    user: hikari.User,                # → from interaction option "user"
    reason: str,                      # → from interaction option "reason"
    db: Database = inject(),          # → from DI container
    logger: Logger = inject(),        # → from DI container
) -> None:
    ...
```

**Resolution rules**:
1. Parameter type is `InteractionContext` → resolve from scope
2. Parameter name matches a command option → extract from interaction
3. Default is `inject()` → resolve from DI container
4. Parameter type is registered in container → resolve from DI
5. Otherwise → error (unknown parameter)

### 4.2 Scope Lifecycle

```
Request arrives
    ↓
ScopeManager created (empty)
    ↓
InteractionContext stored in scope
    ↓
Middleware runs (may add more scoped values)
    ↓
Handler called (parameters resolved from scope + interaction)
    ↓
Handler completes (or error)
    ↓
ScopeManager.cleanup() — all scoped resources released
```

### 4.3 Scoping Rules

| Registration | Lifetime | Use Case |
|---|---|---|
| `@container.singleton` | App-wide, created once | Database pool, cache client |
| `@container.factory` | Per-request, created each time | HTTP session, temp connection |
| `scope.set()` | Per-request, explicit | InteractionContext, request ID |
| `value()` | App-wide, pre-built | Config objects, constants |

---

## 5. Plugin System — Discovery and Loading

### 5.1 Discovery Flow

```
client.load_plugins("plugins/")
    ↓
PluginManager.load_all(Path("plugins/"))
    ↓
PluginLoader.discover(Path("plugins/"), pattern="*.py")
    → Returns: [Path("plugins/fun.py"), Path("plugins/mod.py"), ...]
    ↓
For each path:
    PluginLoader.load_module(path)
        → importlib.util.spec_from_file_location(name, path)
        → importlib.util.module_from_spec(spec)
        → spec.loader.exec_module(module)
    ↓
    PluginLoader.find_setup(module)
        → Look for module.setup (function)
        → Or module that implements Plugin protocol
    ↓
    setup(client)
        → Plugin registers commands/events via decorators
        → Decorators push to global CommandRegistry + EventDispatcher
    ↓
    PluginManager tracks: LoadedPlugin(name, path, module, commands, listeners)
```

### 5.2 Hot-Reload Flow

```
PluginManager.reload("fun")
    ↓
1. PluginManager.unload("fun")
    → Call plugin.on_unload(client)
    → Deregister commands from CommandRegistry
    → Deregister listeners from EventDispatcher
    → Remove from _loaded dict
    ↓
2. Clear import cache: del sys.modules["plugins.fun"]
    ↓
3. PluginManager.load(Path("plugins/fun.py"))
    → Same as initial load
    ↓
4. Re-sync commands with Discord (if any changed)
```

### 5.3 Plugin Structure Example

```python
# plugins/fun.py
import sosad
from sosad import InteractionContext

@sosad.slash_command("8ball", "Ask the magic 8-ball")
@sosad.cooldown(1, 10, bucket=sosad.BucketScope.USER)
async def eight_ball(ctx: InteractionContext, question: str) -> None:
    import random
    responses = ["Yes", "No", "Maybe", "Ask again later"]
    await ctx.respond().content(random.choice(responses)).send()

def setup(client: sosad.Client) -> None:
    """Called when plugin is loaded. Commands are registered via decorators above."""
    pass  # Decorators already registered at import time
```

---

## 6. Command Sync Strategy

### 6.1 Sync Algorithm

```
1. Fetch all global commands from Discord (REST API)
2. Fetch all guild commands for each configured guild
3. Build diff:
    a. Local has command, remote doesn't → CREATE
    b. Local has command, remote has different version → UPDATE
    c. Remote has command, local doesn't → DELETE (if delete_orphans)
    d. Same → UNCHANGED
4. Execute batch REST calls:
    a. Bulk create (POST /applications/{id}/commands)
    b. Individual update (PATCH /applications/{id}/commands/{id})
    c. Individual delete (DELETE /applications/{id}/commands/{id})
5. Return SyncResult with counts
```

### 6.2 Sync Timing

- **Startup**: Always sync before connecting to gateway
- **Plugin reload**: Sync commands for that plugin only
- **Manual**: `client.sync_commands()` public method
- **Development mode**: `client.start(dev_mode=True)` → sync on every plugin reload

### 6.3 Sync Optimization

- Command metadata includes a hash of (name, description, options, permissions)
- Compare hashes instead of full objects for faster diff
- Batch operations where possible (bulk create/update)

---

## 7. Module Dependency Graph

```
                    ┌─────────┐
                    │  utils   │  (no internal deps)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │  core/   │  depends on: utils
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼────┐ ┌───▼───┐ ┌───▼───┐
         │context/ │ │  di/  │ │events/│  (depend on: core, utils)
         └────┬────┘ └───┬───┘ └───┬───┘
              │          │         │
              │    ┌─────▼─────┐   │
              │    │middleware/ │   │  depends on: context, di
              │    └─────┬─────┘   │
              │          │         │
         ┌────▼──────────▼─────────▼────┐
         │         commands/              │  depends on: context, di, middleware, events
         └────────────┬──────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌───▼────┐
    │checks/  │  │cooldowns│  │errors/ │  depend on: context, di
    └────┬────┘  └────┬────┘  └───┬────┘
         │            │            │
    ┌────▼────────────▼────────────▼────┐
    │          permissions/              │  depends on: context
    └────────────┬──────────────────────┘
                 │
    ┌────────────▼────────────┐
    │        plugins/          │  depends on: commands, events, di, middleware
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │     core/client.py       │  depends on: ALL (composition root)
    └─────────────────────────┘
```

**Coupling rules**:
- Lower layers NEVER import upper layers
- `utils/` imports nothing from sosad
- `core/` imports only `utils/`
- `context/` imports `core/` and `utils/`
- `di/` imports `core/` and `utils/`
- `middleware/` imports `context/` and `di/`
- `commands/` imports `context/`, `di/`, `middleware/`, `events/`
- `plugins/` imports `commands/`, `events/`, `di/`, `middleware/`
- `client.py` imports everything (it's the composition root)

---

## 8. Implementation Order

### Phase 1: Foundation (Week 1)
Build the minimal skeleton that can receive an interaction and respond.

| Priority | Module | Why First |
|---|---|---|
| 1 | `utils/` | Zero deps, needed by everything |
| 2 | `core/constants.py` | Sentinels, enums |
| 3 | `core/app.py` | Application state |
| 4 | `context/context.py` | Core abstraction — immutable ctx + builder |
| 5 | `core/client.py` | Entry point (minimal: just GatewayBot wrapper) |

**Deliverable**: A minimal client that connects to Discord and can send a "hello world" response.

### Phase 2: Command System (Week 2)
The decorator API and routing.

| Priority | Module | Why |
|---|---|---|
| 6 | `commands/models.py` | Metadata dataclasses |
| 7 | `commands/registration.py` | Global registry |
| 8 | `commands/decorators.py` | `@slash_command()` API |
| 9 | `commands/registry.py` | Command tree + resolution |
| 10 | `commands/router.py` | Routes interactions to handlers |
| 11 | `commands/sync.py` | Sync to Discord |

**Deliverable**: A working slash command that can be registered via decorator, synced to Discord, and executed.

### Phase 3: Middleware + DI (Week 3)
The pipeline and dependency injection.

| Priority | Module | Why |
|---|---|---|
| 12 | `di/container.py` | Core DI |
| 13 | `di/scopes.py` | Per-request scoping |
| 14 | `di/providers.py` | Registration helpers |
| 15 | `di/markers.py` | `inject()` |
| 16 | `middleware/types.py` | Protocol definitions |
| 17 | `middleware/registry.py` | Pipeline builder |
| 18 | `middleware/builtins.py` | Logging, auto-defer |

**Deliverable**: Middleware pipeline works. DI resolves dependencies in handlers.

### Phase 4: Events (Week 3-4)
Typed event system.

| Priority | Module | Why |
|---|---|---|
| 19 | `events/models.py` | Event metadata |
| 20 | `events/typed.py` | `@listen()` decorator |
| 21 | `events/dispatcher.py` | Event routing |

**Deliverable**: `@sosad.listen(hikari.GuildMessageCreateEvent)` works.

### Phase 5: Checks + Cooldowns + Permissions (Week 4)
Pre-conditions and rate limiting.

| Priority | Module | Why |
|---|---|---|
| 22 | `checks/base.py` | Check protocol |
| 23 | `checks/decorator.py` | `@check()` |
| 24 | `checks/builtin.py` | Common checks |
| 25 | `cooldowns/buckets.py` | Bucket scopes |
| 26 | `cooldowns/storage.py` | Cooldown storage |
| 27 | `cooldowns/decorator.py` | `@cooldown()` |
| 28 | `permissions/resolver.py` | Permission resolution |
| 29 | `permissions/decorator.py` | `@requires_permissions()` |

**Deliverable**: Checks, cooldowns, and permission checks work as decorators.

### Phase 6: Error Handling (Week 4-5)
Error pipeline.

| Priority | Module | Why |
|---|---|---|
| 30 | `errors/base.py` | Exception hierarchy |
| 31 | `errors/builtin.py` | Built-in errors |
| 32 | `errors/handler.py` | Error pipeline |

**Deliverable**: Errors are caught, typed, and handled gracefully.

### Phase 7: Plugins (Week 5)
Module loading and hot-reload.

| Priority | Module | Why |
|---|---|---|
| 33 | `plugins/base.py` | Plugin protocol |
| 34 | `plugins/loader.py` | Module discovery |
| 35 | `plugins/manager.py` | Lifecycle management |

**Deliverable**: `client.load_plugins("plugins/")` works. Hot-reload works.

### Phase 8: Polish (Week 5-6)
CLI, docs, edge cases.

| Priority | Module | Why |
|---|---|---|
| 36 | `cli/runner.py` | `python -m sosad` |
| 37 | `__init__.py` | Public API exports |
| 38 | Tests | Pytest + pytest-asyncio |
| 39 | Documentation | API reference + guides |

---

## 9. Key Design Tradeoffs

### Tradeoff 1: Immutable Context vs Mutable Context
- **Chosen**: Immutable (frozen dataclass)
- **Why**: Eliminates shared-state bugs. Response building is explicit. Easier to reason about in concurrent contexts.
- **Cost**: More object allocation. Response builder creates new instances per method call.
- **Mitigation**: Builder instances are lightweight. Allocation cost is negligible vs network I/O.

### Tradeoff 2: Pipeline Middleware vs Hook System
- **Chosen**: Flat pipeline (ASGI-style)
- **Why**: Simpler mental model. Each middleware is a function wrapping the next. Easy to reason about execution order. No hook ordering bugs.
- **Cost**: No parallel execution of middleware. Less flexible than a tree.
- **Mitigation**: Discord interactions are sequential (one handler per request). Parallelism isn't needed.

### Tradeoff 3: Function-based Registration vs Class-based
- **Chosen**: Function-based decorators returning metadata
- **Why**: Simpler API. No class boilerplate. Metadata is data, not behavior. Decorators compose naturally.
- **Cost**: Less structure for large command sets. No natural grouping via classes.
- **Mitigation**: Command groups provide structure. Plugins organize related commands.

### Tradeoff 4: Annotation-based DI vs Explicit Depends()
- **Chosen**: Annotation-based with `inject()` disambiguator
- **Why**: Less boilerplate. Parameters are self-documenting via types. Familiar from FastAPI.
- **Cost**: Potential collision between DI types and command option names.
- **Mitigation**: `inject()` marker forces DI resolution when ambiguous. Naming conventions help.

### Tradeoff 5: Reusing Hikari Events vs Custom Events
- **Chosen**: Reuse Hikari event types directly
- **Why**: No translation layer. Compatible with Hikari ecosystem. Less code to maintain.
- **Cost**: Less abstraction over Discord events. Users interact with Hikari types directly.
- **Mitigation**: Convenience properties on `InteractionContext` provide higher-level access.

### Tradeoff 6: Composition vs Inheritance for Client
- **Chained**: Composition (Client owns GatewayBot)
- **Why**: Clean separation. Hikari internals never leak into SoSad's API. Easier to swap Hikari in the future (unlikely but possible).
- **Cost**: More forwarding code in Client.
- **Mitigation**: Only forward methods users actually need. Lazy forwarding via `__getattr__`.

### Tradeoff 7: Global Registry vs Per-Client Registry
- **Chosen**: Global registry (module-level)
- **Why**: Simpler. Decorators run at import time. No need to pass client reference to every decorator.
- **Cost**: Multiple Client instances share the same registry (problematic for testing).
- **Mitigation**: `CommandRegistry` can be instantiated per-client for testing. Global is for convenience.

---

## 10. Future Interfaces (Design Only)

### Components (Buttons, Select Menus, Modals)
```python
@sosad.component(hikari.ButtonStyle.PRIMARY, label="Click Me")
async def my_button(ctx: ComponentContext) -> None:
    await ctx.respond().content("Clicked!").send()

@sosad.modal("My Form")
class MyModal:
    name: str = sosad.modal_field(label="Name", style=hikari.TextInputStyle.SHORT)
    bio: str = sosad.modal_field(label="Bio", style=hikari.TextInputStyle.PARAGRAPH)

    async def on_submit(self, ctx: ModalContext) -> None:
        ...
```

### File Upload
```python
await ctx.respond().file(hikari.File("path/to/image.png")).send()
await ctx.respond().files(hikari.File(io.BytesIO(data), filename="data.csv")).send()
```

### Voice
```python
@sosad.slash_command("join", "Join your voice channel")
async def join(ctx: InteractionContext) -> None:
    state = ctx.author_voice_state
    if state is None:
        await ctx.respond().content("Join a voice channel first!").ephemeral().send()
        return
    await ctx.client.voice.join(state.channel_id)
```

### Tasks / Scheduler
```python
@sosad.task(interval=300)  # every 5 minutes
async def cleanup_task(app: App) -> None:
    db = app.resolve(Database)
    await db.cleanup_old_records()
```
