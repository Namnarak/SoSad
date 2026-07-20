"""Example 4: Components — Views, Buttons, Modals, Paginator.

Run:
    TOKEN=your_token python examples/component_bot.py
"""

from __future__ import annotations

import os

import hikari

import sosad

bot = sosad.Client(
    token=os.environ["TOKEN"],
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)


# ── Button example ────────────────────────────────────────
@sosad.slash_command("greet", "Greet with a button")
async def greet(ctx: sosad.InteractionContext) -> None:
    view = sosad.View()
    view.add_button("welcome", "Say Hi!", sosad.ButtonBuilder.PRIMARY)
    await ctx.respond("Click the button!").set_components(view).send()


@sosad.components.button("welcome")
async def on_welcome(ctx: sosad.ComponentContext) -> None:
    await ctx.respond(f"Hi {ctx.author.mention}!")


# ── Select menu example ───────────────────────────────────
@sosad.slash_command("choose", "Pick an option")
async def choose(ctx: sosad.InteractionContext) -> None:
    view = sosad.View()
    view.add_select(
        "color",
        "Pick a color",
        options=[
            ("Red", "red"),
            ("Green", "green"),
            ("Blue", "blue"),
        ],
    )
    await ctx.respond("Choose a color:").set_components(view).send()


@sosad.components.select("color")
async def on_color(ctx: sosad.ComponentContext) -> None:
    color = ctx.values[0]
    await ctx.respond(f"You picked **{color}**!")


# ── Modal example ─────────────────────────────────────────
@sosad.slash_command("feedback", "Submit feedback")
async def feedback(ctx: sosad.InteractionContext) -> None:
    modal = sosad.Modal("feedback_modal", "Feedback Form")
    modal.add_text_input(
        "name",
        "Your name",
        min_length=1,
        max_length=100,
    )
    modal.add_text_input(
        "message",
        "Your feedback",
        style=hikari.TextInputStyle.PARAGRAPH,
    )
    await ctx.respond_with_modal(modal)


@sosad.components.modal("feedback_modal")
async def on_feedback(ctx: sosad.ComponentContext) -> None:
    name = ctx.values["name"]
    message = ctx.values["message"]
    embed = hikari.Embed(
        title="Feedback Received",
        colour=0x00FF00,
    )
    embed.add_field(name="Name", value=name)
    embed.add_field(name="Message", value=message)
    await ctx.respond(embed=embed)


# ── Paginator example ─────────────────────────────────────
from sosad.components import Paginator


@Paginator.register("help_pages")
class HelpPaginator(Paginator):
    def __init__(self) -> None:
        super().__init__(pages=[
            {"title": "Commands", "desc": "/ping, /hello, /echo"},
            {"title": "Components", "desc": "/greet, /choose, /feedback"},
            {"title": "Settings", "desc": "/config view, /config set"},
        ])

    async def render_page(self, page: dict) -> sosad.ResponseBuilder:
        embed = hikari.Embed(
            title=page["title"],
            description=page["desc"],
            colour=0x9B59B6,
        )
        return sosad.ResponseBuilder().embed(embed)


@sosad.slash_command("help", "Show help pages")
async def help_cmd(ctx: sosad.InteractionContext) -> None:
    paginator = HelpPaginator()
    paginator.bind(ctx)
    await paginator.send(ctx)


if __name__ == "__main__":
    bot.run()
