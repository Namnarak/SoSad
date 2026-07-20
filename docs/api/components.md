# Components API Reference

## View

```python
from sosad import View

view = View()
view.add_button(custom_id, label, style)
view.add_select(custom_id, placeholder, options)
view.add_link_button(label, url)
```

## PersistentView

```python
from sosad.components import PersistentView

@PersistentView.register("my_view", timeout=3600)
class MyView(PersistentView):
    def __init__(self) -> None:
        super().__init__()
        self.add_button("action", "Click", ButtonBuilder.PRIMARY)

    async def on_button(self, ctx: ComponentContext, button_id: str) -> None:
        ...
```

## Paginator

```python
from sosad.components import Paginator

@Paginator.register("help_pages")
class HelpPaginator(Paginator):
    async def render_page(self, page: dict) -> ResponseBuilder:
        ...

paginator = HelpPaginator()
paginator.bind(ctx)
await paginator.send(ctx)
```

## Modals

```python
from sosad import Modal

modal = Modal("feedback", "Feedback")
modal.add_text_input(
    custom_id="message",
    label="Your message",
    style=hikari.TextInputStyle.PARAGRAPH,
    min_length=1,
    max_length=1000,
)
await ctx.respond_with_modal(modal)
```

## Storage

```python
from sosad.components.storage import (
    ViewStorage,
    InMemoryViewStorage,
    FileViewStorage,
    set_view_storage,
    get_view_storage,
)
```
