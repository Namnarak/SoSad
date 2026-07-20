# Context

## InteractionContext

The context object provides access to the interaction data.

### Properties

| Property | Type | Description |
|---|---|---|
| `author` | `hikari.User` | Who invoked the command |
| `guild_id` | `Snowflake \| None` | Guild ID (None in DMs) |
| `channel_id` | `Snowflake` | Channel ID |
| `options` | `dict[str, Option]` | All options as a dict |
| `interaction` | `CommandInteraction` | Raw Hikari interaction |
| `client` | `Client` | The SoSad client |
| `app` | `App` | Application state |

### Getting options

```python
# By name
user = ctx.get_user("user")
reason = ctx.get_str("reason")
count = ctx.get_int("count")

# With default
value = ctx.get_option("optional_param", default="fallback")
```

## Response Patterns

### Shortcut (simple)

```python
await ctx.respond("Pong!")
await ctx.respond("Hello!", ephemeral=True)
```

### Builder (complex)

```python
await (
    ctx.respond()
    .content("Done!")
    .ephemeral()
    .embed(embed)
    .file(file)
    .send()
)
```

### Builder methods

| Method | Description |
|---|---|
| `.content(text)` | Set message content |
| `.embed(embed)` | Add an embed |
| `.embeds(*embeds)` | Add multiple embeds |
| `.file(file)` | Add a file |
| `.files(*files)` | Add multiple files |
| `.ephemeral()` | Make ephemeral |
| `.flag(flag)` | Add a message flag |
| `.send()` | Execute the response |
| `.defer()` | Defer the response |

### Defer

```python
# For long-running commands
await ctx.defer()

# Defer as ephemeral
await ctx.defer(ephemeral=True)
```

### Edit response

```python
await ctx.edit_response(content="Updated!")
```

## ComponentContext

For button clicks, select menus, and modal submissions:

```python
from sosad.components.base import ComponentContext

async def on_button(ctx: ComponentContext):
    print(ctx.custom_id)  # "my_button"
    print(ctx.values)     # [] for buttons, ["value"] for selects
    await ctx.respond("Clicked!").ephemeral()
```

### Properties

| Property | Type | Description |
|---|---|---|
| `custom_id` | `str` | The component's custom_id |
| `values` | `list[str]` | Selected values (select only) |
| `component_type` | `ComponentType` | Button, Select, etc. |
| `author` | `hikari.User` | Who clicked |
| `guild_id` | `Snowflake \| None` | Guild ID |
| `channel_id` | `Snowflake` | Channel ID |
