# SoSad

<div class="hero" markdown>

**Drop in. Scale up.**

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari).

Change one line. Get production-ready features instantly.

```python
import sosad.compat as discord  # ← that's it

bot = discord.Bot(intents=hikari.Intents.ALL_UNPRIVILEGED)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

bot.run("TOKEN")
```

[Get Started](guides/installation.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/Namnarak/SoSad){ .md-button }

</div>

---

## Why SoSad?

### For discord.py refugees

| Feature | discord.py | SoSad |
|---|---|---|
| Rate limiting | Manual retry | Automatic per-route |
| Error handling | try/except | Error pipeline |
| Dependency Injection | None | FastAPI-style container |
| Middleware | Before/After hooks | ASGI-style pipeline |
| Plugins | Manual `load_extension` | Auto-discover |
| Config | `os.getenv` | `pydantic-style Settings` |
| Type safety | Partial | Pyright strict |
| REST mode | ❌ | ✅ (no gateway needed) |
| Persistent Components | ❌ | ✅ (survive restarts) |
| Task scheduler | ❌ | ✅ (cron-like) |
| CLI scaffold | ❌ | ✅ (`sosad new`) |

### For new projects

```python
import hikari
import sosad

class Config(sosad.Settings):
    token: str

bot = sosad.Client(token=Config().token, intents=hikari.Intents.ALL_UNPRIVILEGED)

@sosad.slash_command("ping", "Pong!")
async def ping(ctx: sosad.InteractionContext):
    await ctx.respond("Pong!")

bot.run()
```

---

## Quick install

```bash
pip install sosad
# or
uv add sosad
```

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    Your Code                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Commands  │  │ Plugins   │  │  Components     │  │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
├───────┴─────────────┴─────────────────┴──────────┤
│                    SoSad Core                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Router   │  │Middleware│  │  DI Container   │  │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       └─────────────┴─────────────────┘           │
│  ┌──────────────────────────────────────────────┐  │
│  │              Hikari (transport)               │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## Features

<div class="grid cards" markdown>

- :material-speedometer:{ .lg .middle } **Auto Rate Limiting**

    ---

    Per-route rate limiting. No more HTTP 429s. Works for both Gateway and REST mode.

    [:octicons-arrow-right-24: Getting Started](guides/installation.md)

- :material-shield-lock:{ .lg .middle } **Type Safe**

    ---

    Full type hints. Pyright strict mode. Catch errors before runtime.

    [:octicons-arrow-right-24: Commands](guides/commands.md)

- :material-puzzle:{ .lg .middle } **Modular Plugins**

    ---

    Drop files in `plugins/` — auto-discovered and loaded.

    [:octicons-arrow-right-24: Plugins](guides/plugins.md)

- :material-cog:{ .lg .middle } **DI + Middleware**

    ---

    FastAPI-style dependency injection. ASGI-inspired middleware pipeline.

    [:octicons-arrow-right-24: Middleware](guides/middleware.md)

- :material-view-grid:{ .lg .middle } **Components**

    ---

    Buttons, Select Menus, Modals, Persistent Views, Paginator.

    [:octicons-arrow-right-24: Components](guides/components.md)

- :material-clock:{ .lg .middle } **Background Tasks**

    ---

    Decorator-based task scheduler with intervals and CRON-like triggers.

    [:octicons-arrow-right-24: Tasks](guides/tasks.md)

- :material-api:{ .lg .middle } **REST Mode**

    ---

    Run without a gateway. Perfect for webhooks, microservices, and serverless.

    [:octicons-arrow-right-24: REST API](guides/rest.md)

- :material-swap-horizontal:{ .lg .middle } **discord.py Compat**

    ---

    Change one import. Keep your existing codebase.

    [:octicons-arrow-right-24: Migration](guides/migration.md)

</div>
