# Client API Reference

## sosad.Client

The main Gateway bot client.

### Constructor

```python
Client(
    *,
    token: str,
    intents: hikari.Intents,
    logs: str | int = "INFO",
    banner: str = "so sad",
    auto_discover_plugins: bool = True,
    sync_commands: bool = True,
    **kwargs,
)
```

### Properties

| Name | Type | Description |
|---|---|---|
| `bot` | `hikari.GatewayBot` | The underlying hikari bot |
| `rest` | `hikari.api.RESTProvider` | REST API access |
| `registry` | `CommandRegistry` | Command registry |
| `container` | `Container` | DI container |
| `prefix` | `str` | Prefix for prefix commands |

### Methods

| Method | Description |
|---|---|
| `run()` | Start the bot (blocking) |
| `close()` | Graceful shutdown |
| `use(middleware)` | Add middleware |
| `on_error(handler)` | Register error handler |
| `listen(event_type)` | Register event listener |
| `load_plugins(path)` | Load plugins from path |
| `load_extension(name)` | Load extension package |
| `task(**kwargs)` | Register background task |

## sosad.RESTClient

REST-mode client (no gateway).

### Constructor

```python
RESTClient(
    *,
    token: str,
    public_key: str | bytes | None = None,
    logs: str | int = "INFO",
    banner: str = "so sad",
    auto_discover_plugins: bool = True,
    **kwargs,
)
```
