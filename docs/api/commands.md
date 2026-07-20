# Commands API Reference

## Decorators

### `sosad.slash_command(name, description)`

Register a slash command.

```python
@sosad.slash_command("ping", "Check latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    ...
```

### `sosad.command_group(name, description)`

Create a command group for subcommands.

```python
group = sosad.command_group("config", "Configuration")

@group.sub_command("view", "View config")
async def config_view(ctx: sosad.InteractionContext) -> None:
    ...
```

### `sosad.components.button(custom_id)`

Register a button handler.

### `sosad.components.select(custom_id)`

Register a select menu handler.

### `sosad.components.modal(custom_id)`

Register a modal handler.

## Annotations

| Annotation | Type | Description |
|---|---|---|
| `sosad.annotations.String` | `str` | String option |
| `sosad.annotations.Integer` | `int` | Integer option |
| `sosad.annotations.Float` | `float` | Float option |
| `sosad.annotations.Boolean` | `bool` | Boolean option |
| `sosad.annotations.User` | `hikari.User` | User option |
| `sosad.annotations.Channel` | `hikari.GuildChannel` | Channel option |
| `sosad.annotations.Role` | `hikari.Role` | Role option |
| `sosad.annotations.Mentionable` | `hikari.User | hikari.Role` | Mentionable |

## Parameter options

```python
@sosad.slash_command("search", "Search")
async def search(
    ctx: sosad.InteractionContext,
    query: str = sosad.annotations.String(
        description="Search query",
        min_length=1,
        max_length=100,
        autocomplete=True,
    ),
    limit: int = sosad.annotations.Integer(
        description="Results limit",
        min_value=1,
        max_value=100,
        default=10,
    ),
) -> None:
    ...
```
