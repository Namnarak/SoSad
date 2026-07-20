# Quick Start

## Create a project

```bash
sosad new mybot
cd mybot
uv sync
```

## Add your token

Edit `.env`:

```
TOKEN=your-discord-bot-token
```

## Run

```bash
uv run bot.py
```

## Project structure

```
mybot/
├── bot.py          # Main bot file
├── plugins/        # Auto-discovered
│   └── example.py
├── pyproject.toml
└── .env
```
