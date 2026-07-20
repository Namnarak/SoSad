# Background Tasks

SoSad has a built-in task scheduler. Tasks run in the background while your bot is running.

## Basic task

```python
from sosad import task

@task(minutes=5)
async def clean_cache() -> None:
    """Clean old cache entries every 5 minutes."""
    cache.clear()
    logger.info("Cache cleaned")
```

## Task intervals

```python
@task(seconds=30)
async def health_check() -> None:
    ...

@task(minutes=15)
async def sync_data() -> None:
    ...

@task(hours=1)
async def backup() -> None:
    ...

@task(days=1)
async def daily_report() -> None:
    ...
```

## Accessing bot services

Tasks can access the client via the global registry:

```python
@task(minutes=5)
async def update_status() -> None:
    from sosad import get_client
    client = get_client()
    await client.bot.update_presence(...)
```

## Via the Bot (compat)

```python
bot = discord.Bot(command_prefix="!", intents=..., token="...")

@bot.task(hours=1)
async def clean_temp():
    """Clean temp files every hour."""
    ...
```

## Scheduler API

```python
from sosad.tasks import TaskScheduler, TaskRegistry

# Create a scheduler
scheduler = TaskScheduler()

# Add a task
@task()
async def my_task():
    ...

# Start/stop
scheduler.start()
scheduler.stop()

# Check running tasks
registry = TaskRegistry()
for task_meta in registry:
    print(task_meta.name)
```

## Use cases

- **Cache invalidation** — clear caches periodically
- **Database maintenance** — vacuum, reindex
- **Status updates** — rotate bot status messages
- **Webhook polling** — check external APIs
- **Daily reports** — send scheduled messages
- **Data sync** — sync with external services
