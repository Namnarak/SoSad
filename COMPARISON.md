# SoSad vs Other Discord Frameworks

> Comparison table: SoSad vs discord.py, lightbulb, interactions.py, hikari

## Architecture

| Feature | SoSad |
|---------|-------|
| Async-first | ✅ |
| Type-safe API | ✅ |
| Dependency Injection | ✅ |
| Middleware Pipeline | ✅ |
| Gateway Mode | ✅ |
| REST Mode | ✅ |
| Plugin Loader | ✅ |
| Auto Discovery | ✅ |
| Lifecycle Events | ✅ |
| Extension System | ✅ |
| Context Injection | ✅ |
| Builder Pattern | ✅ |
| Pyright Strict | ✅ |

## Feature Comparison

| Feature | SoSad | discord.py | lightbulb | interactions.py | hikari |
|---------|-------|------------|-----------|-----------------|--------|
| **Python Version** | 3.12+ | 3.8+ | 3.10+ | 3.10+ | 3.10+ |
| **Type Safety** | ✅ Pyright strict | ⚠️ Partial | ✅ Pyright | ✅ Pyright | ✅ Pyright |
| **Slash Commands** | ✅ Native | ✅ app_commands | ✅ Native | ✅ Native | ⚠️ Manual |
| **Prefix Commands** | ✅ `!ping` | ✅ `!ping` | ✅ `!ping` | ❌ No | ⚠️ Manual |
| **Components** | ✅ Builder | ✅ ui module | ✅ Builder | ✅ Native | ⚠️ Manual |
| **Persistent Views** | ✅ Built-in | ⚠️ Requires registration | ⚠️ Requires registration | ⚠️ Requires registration | ❌ No |
| **Paginator** | ✅ Built-in | ❌ No | ❌ No | ❌ No | ❌ No |
| **DI Container** | ✅ FastAPI-style | ❌ No | ❌ No | ❌ No | ❌ No |
| **Middleware** | ✅ ASGI-style | ⚠️ Event hooks | ⚠️ Event hooks | ❌ No | ❌ No |
| **Plugin System** | ✅ Auto-discover | ⚠️ Manual | ✅ Auto-discover | ✅ Extensions | ❌ No |
| **Background Tasks** | ✅ `@sosad.task` | ✅ `@tasks.loop` | ✅ `@task` | ✅ Task extension | ❌ No |
| **REST Mode** | ✅ Serverless | ❌ No | ❌ No | ❌ No | ✅ RESTBot |
| **Rate Limiting** | ✅ Auto per-route [See docs](https://sosad.dev/guides/middleware/#rate-limiting) | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic |
| **Error Pipeline** | ✅ Typed exception pipeline | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic | ❌ No |
| **Cooldown System** | ✅ Bucket-based | ✅ `@cooldown` | ✅ `@cooldown` | ❌ No | ❌ No |
| **Permission Checks** | ✅ Decorators | ✅ `@has perms` | ✅ `@has perms` | ✅ Native | ⚠️ Manual |
| **CLI Scaffold** | ✅ `sosad init` | ❌ No | ❌ No | ✅ `interactions init` | ❌ No |
| **discord.py Compat** | ✅ High compatibility | ✅ Native | ❌ No | ❌ No | ❌ No |
| **Hikari Native** | ✅ Full access | ❌ No | ✅ Full access | ❌ No | ✅ Core library |
| **Serverless Ready** | ✅ REST mode | ❌ No | ❌ No | ❌ No | ✅ RESTBot |

## Code Comparison

### Slash Command

```python
# SoSad
@sosad.slash_command("ping", "Check bot latency")
async def ping(ctx: sosad.InteractionContext) -> None:
    await ctx.respond("Pong!").send()

# discord.py
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong!")

# lightbulb
@bot.command
@lightbulb.command("ping", "Check bot latency")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    await ctx.respond("Pong!")
```

### Persistent View

```python
# SoSad
view = PersistentView(timeout=60.0)
view.button(custom_id="confirm", label="Confirm")

@view.on_click("confirm")
async def on_confirm(ctx):
    await ctx.respond("Confirmed!").send()

await ctx.respond().components(view).send()

# discord.py
class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
    
    @discord.ui.button(label="Confirm")
    async def confirm(self, interaction, button):
        await interaction.response.send_message("Confirmed!")

# Note: discord.py requires manual registration with bot.add_view()
```

### Dependency Injection

```python
# SoSad
class Database:
    def __init__(self):
        self.connected = True

bot.container.singleton(Database)

@sosad.slash_command("check_db", "Check database")
async def check_db(ctx: sosad.InteractionContext, db: Database) -> None:
    # db auto-resolved
    await ctx.respond(f"DB: {db.connected}")

# discord.py / lightbulb - No built-in DI
# Must pass dependencies manually or use global variables
```

## When to Use Which

| Use Case | Recommended Framework |
|----------|----------------------|
| **New project, need DI + middleware** | SoSad |
| **Existing discord.py project** | SoSad (compat layer) |
| **Simple bot, minimal features** | discord.py or lightbulb |
| **Serverless deployment** | SoSad or hikari |
| **Maximum type safety** | SoSad or lightbulb |
| **Community plugins/ecosystem** | discord.py |
| **Performance critical** | hikari |

## SoSad Key Features

1. **discord.py Compatibility Layer** - High compatibility with common discord.py APIs, designed to ease migration
2. **Persistent Views + Paginator** - Built-in stateful components
3. **FastAPI-style DI** - Auto-resolve dependencies by type
4. **ASGI Middleware Pipeline** - Before/after/short-circuit
5. **REST Mode** - Serverless-ready architecture
6. **CLI Scaffold** - `sosad init mybot` ready in seconds
7. **Plugin Auto-Discovery** - Drop files in `plugins/`, done
8. **Auto Rate Limiting** - Per-route bucket tracking

## Migration Guide

### discord.py → SoSad

```python
# BEFORE (discord.py)
import discord
bot = discord.Client(intents=discord.Intents.default())

# AFTER (SoSad) - change 1 line
import sosad.compat as discord
bot = discord.Bot(intents=discord.Intents.default())
```

### hikari → SoSad

```python
# BEFORE (hikari)
import hikari
bot = hikari.GatewayBot(token="...")

# AFTER (SoSad)
import sosad
bot = sosad.Client(token="...", intents=hikari.Intents.ALL_UNPRIVILEGED)
```

## Conclusion

SoSad combines modern framework features such as dependency injection, middleware, persistent UI components and REST deployment into a single Discord framework while maintaining a familiar developer experience.
