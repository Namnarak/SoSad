# Events

## Listening to events

```python
import hikari

@sosad.listen(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    print(f"Message from {event.author}: {event.content}")

@sosad.listen(hikari.GuildMemberCreateEvent)
async def on_member_join(event: hikari.GuildMemberCreateEvent) -> None:
    print(f"{event.user} joined {event.guild_id}")
```

## Via the Client

```python
bot = sosad.Client(token="...", intents=hikari.Intents.ALL)

@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    print("Bot is ready!")
```

## Event priority

Events are dispatched in registration order. Use middleware for ordering.

## Typed events

```python
from sosad.events import TypedEvent

class UserMessageEvent(TypedEvent):
    user_id: int
    content: str
    channel_id: int

# Emit
await UserMessageEvent(user_id=123, content="Hello!", channel_id=456).emit()

# Listen
@sosad.listen(UserMessageEvent)
async def on_user_message(event: UserMessageEvent) -> None:
    print(f"{event.user_id}: {event.content}")
```

## Discord.py compat

```python
bot = discord.Bot(command_prefix="!", intents=..., token="...")

@bot.event
async def on_ready():
    print("Ready!")

@bot.listen()
async def on_message(event: hikari.MessageCreateEvent):
    print(f"Message: {event.content}")
```
