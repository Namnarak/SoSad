# Checks & Cooldowns

## Checks

### Built-in checks

```python
from sosad import guild_only, dm_only, is_owner, has_permissions

@sosad.slash_command("admin", "Admin only")
@guild_only
@is_owner
async def admin_only(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Welcome, owner!")

@sosad.slash_command("kick", "Kick a user")
@has_permissions(kick_members=True)
async def kick(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("You can kick!")
```

### Custom checks

```python
from sosad import check, CheckResult

def is_premium() -> CheckResult:
    async def check_fn(ctx: sosad.InteractionContext) -> bool:
        return ctx.author.id in PREMIUM_USERS
    return check("premium", check_fn)

@sosad.slash_command("premium", "Premium feature")
@is_premium()
async def premium_cmd(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Premium content!")
```

## Cooldowns

### Rate limit by user

```python
from sosad import cooldown, BucketScope

@sosad.slash_command("spam", "Can't spam")
@cooldown(1, 5, BucketScope.USER)  # 1 use per 5 seconds per user
async def spam(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Not so fast!")
```

### Bucket scopes

```python
@cooldown(5, 60, BucketScope.USER)       # Per user
@cooldown(10, 60, BucketScope.CHANNEL)    # Per channel
@cooldown(20, 60, BucketScope.GUILD)      # Per guild
@cooldown(100, 60, BucketScope.GLOBAL)    # Global
```

### Custom cooldown message

```python
from sosad import CooldownConfig

@sosad.slash_command("slow", "Slow command")
@cooldown(1, 10, BucketScope.USER, config=CooldownConfig(
    error_message="Please wait {remaining:.0f}s",
))
async def slow(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Done!")
```
