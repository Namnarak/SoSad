# SoSad

<div class="hero" markdown>

**Drop in. Scale up.**

A modern, modular, type-safe Discord framework built on [Hikari](https://github.com/hikari-py/hikari).

Change one line. Get production-ready features instantly.

```python
import sosad.compat as discord  # ← that's it

bot = discord.Bot(intents=discord.Intents.default())

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

### For hobby bots → production

| Feature | discord.py | SoSad |
|---|---|---|
| Rate limiting | Manual | Automatic |
| Error handling | try/except | Pipeline |
| DI | None | FastAPI-style |
| Middleware | Before/After | ASGI pipeline |
| Plugins | Manual | Auto-discover |
| Config | .env manual | `class Config(sosad.Settings)` |
| Type safety | Partial | Full strict |

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

## Features

<div class="grid cards" markdown>

- :material-speedometer:{ .lg .middle } **Fast**

    ---

    Auto rate limiting per-route. No more HTTP 429s.

    [:octicons-arrow-right-24: Getting Started](guides/installation.md)

- :material-shield-lock:{ .lg .middle } **Safe**

    ---

    Full type hints. Pyright strict. Catch errors before runtime.

    [:octicons-arrow-right-24: Commands](guides/commands.md)

- :material-puzzle:{ .lg .middle } **Modular**

    ---

    Plugin auto-discovery. Drop files in `plugins/`, done.

    [:octicons-arrow-right-24: Plugins](guides/plugins.md)

- :material-cog:{ .lg .middle } **Powerful**

    ---

    DI, middleware, components, background tasks. All included.

    [:octicons-arrow-right-24: Middleware](guides/middleware.md)

