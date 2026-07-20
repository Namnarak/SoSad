# Components (View/Modal)

## Basic Button

```python
import sosad

@sosad.slash_command("hello", "Say hello with a button")
async def hello(ctx: sosad.InteractionContext) -> None:
    view = sosad.View()
    view.add_button("click", "Click me!", sosad.ButtonBuilder.PRIMARY)
    await ctx.respond("Hello!").set_components(view).send()

@sosad.components.button("click")
async def on_click(ctx: sosad.ComponentContext) -> None:
    await ctx.respond("Button clicked!")
```

## Select Menu

```python
view = sosad.View()
view.add_select(
    "choose",
    "Pick an option",
    options=[
        ("Option A", "a"),
        ("Option B", "b"),
    ],
)
await ctx.respond("Choose:").set_components(view).send()

@sosad.components.select("choose")
async def on_select(ctx: sosad.ComponentContext) -> None:
    await ctx.respond(f"You picked: {ctx.values}")
```

## Modal

```python
@sosad.slash_command("feedback", "Submit feedback")
async def feedback(ctx: sosad.InteractionContext) -> None:
    modal = sosad.Modal("feedback_modal", "Feedback")
    modal.add_text_input("message", "Your message", style=hikari.TextInputStyle.PARAGRAPH)
    await ctx.respond_with_modal(modal)

@sosad.components.modal("feedback_modal")
async def on_feedback(ctx: sosad.ComponentContext) -> None:
    message = ctx.values["message"]
    await ctx.respond(f"Thanks! You said: {message}")
```

## Persistent Views

Views that survive bot restarts. State is stored and restored automatically.

```python
from sosad.components import PersistentView
from sosad.components.storage import FileViewStorage, set_view_storage

# Enable file-based persistence (survives restarts)
set_view_storage(FileViewStorage("views_data"))

@PersistentView.register("ticket_view", timeout=3600)
class TicketView(PersistentView):
    def __init__(self, ticket_id: str) -> None:
        super().__init__()
        self.ticket_id = ticket_id
        self.add_button("close", "Close Ticket", sosad.ButtonBuilder.DANGER)
        self.add_button("claim", "Claim", sosad.ButtonBuilder.SECONDARY)

    # Auto-wired handler
    async def on_button(self, ctx: sosad.ComponentContext, button_id: str) -> None:
        if button_id == "close":
            await ctx.respond("Ticket closed!")
        elif button_id == "claim":
            await ctx.respond("Ticket claimed!")

# Usage in command
async def create_ticket(ctx: sosad.InteractionContext) -> None:
    view = TicketView(ticket_id=str(uuid4()))
    view.bind(ctx)  # Attach to context
    await ctx.respond("Ticket created!").set_components(view).send()
```

## Paginator

```python
from sosad.components import Paginator

@Paginator.register("help_pages")
class HelpPaginator(Paginator):
    def __init__(self) -> None:
        super().__init__(pages=[
            {"title": "Page 1", "description": "Commands list..."},
            {"title": "Page 2", "description": "More commands..."},
            {"title": "Page 3", "description": "Settings..."},
        ])

    async def render_page(self, page: dict) -> sosad.ResponseBuilder:
        embed = hikari.Embed(title=page["title"], description=page["description"])
        return sosad.ResponseBuilder().set_embed(embed)

# Usage
@sosad.slash_command("help", "Show help")
async def help_cmd(ctx: sosad.InteractionContext) -> None:
    paginator = HelpPaginator()
    paginator.bind(ctx)
    await paginator.send(ctx)
```

## Storage backends

```python
# In-memory (default — lost on restart)
from sosad.components.storage import InMemoryViewStorage, set_view_storage
set_view_storage(InMemoryViewStorage())

# File-based (survives restarts)
from sosad.components.storage import FileViewStorage
set_view_storage(FileViewStorage("views_data"))
```
