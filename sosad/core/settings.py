"""Settings/Config with auto .env loading."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base settings class with auto .env loading.

    Usage::

        class BotConfig(sosad.Settings):
            token: str
            guild_id: int = 0
            debug: bool = False

        config = BotConfig()  # loads from .env automatically
        bot = sosad.Client(token=config.token, intents=...)
    """

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


__all__ = ["Settings"]
