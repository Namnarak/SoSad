# Commands

## Slash Commands

```python
@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!")
```

## Options

Options are extracted from function parameters:

```python
@sosad.slash_command("hello", "Say hello")
async def hello(
    ctx: sosad.InteractionContext,
    user: hikari.User,           # required
    greeting: str = "Hello",     # optional
) -> None:
    await ctx.respond(f"{greeting}, {user.mention}!")
```

### Supported types

| Python type | Discord type |
|---|---|
| `str` | STRING |
| `int` | INTEGER |
| `float` | FLOAT |
| `bool` | BOOLEAN |
| `hikari.User` | USER |
| `hikari.Member` | USER |
| `hikari.GuildChannel` | CHANNEL |
| `hikari.Role` | ROLE |
| `hikari.Attachment` | ATTACHMENT |

### Option descriptions

```python
@sosad.slash_command(
    "ban", "Ban a user",
    option_descriptions={
        "user": "The user to ban",
        "reason": "Reason for the ban",
    },
)
async def ban(ctx, user: hikari.User, reason: str = "No reason"):
    ...
```

## Command Groups

```python
@sosad.command_group("config", "Bot configuration")
async def config(ctx: sosad.InteractionContext) -> None:
    pass

@sosad.sub_command("config", "set", "Set a config value")
async def config_set(ctx, key: str, value: str) -> None:
    await ctx.respond(f"Set {key} = {value}")

@sosad.sub_command("config", "get", "Get a config value")
async def config_get(ctx, key: str) -> None:
    await ctx.respond(f"{key} = {settings[key]}")
```

## Checks

```python
@sosad.slash_command("ban", "Ban a user")
@sosad.check(sosad.has_permissions(hikari.Permissions.BAN_MEMBERS))
async def ban(ctx, user: hikari.User):
    ...
```

## Cooldowns

```python
@sosad.slash_command("work", "Earn coins")
@sosad.cooldown(1, 60, bucket=sosad.BucketScope.USER)
async def work(ctx):
    await ctx.respond("You earned 10 coins!")
```

## Combining checks + cooldowns

```python
@sosad.slash_command("ban", "Ban a user")
@sosad.check(sosad.is_owner())
@sosad.cooldown(1, 10, bucket=sosad.BucketScope.USER)
async def ban(ctx, user: hikari.User):
    ...
```

## Command flags

```python
@sosad.slash_command(
    "secret",
    "A secret command",
    is_dm_only=True,
    nsfw=True,
    default_member_permissions=hikari.Permissions.ADMINISTRATOR,
)
async def secret(ctx):
    ...
```
