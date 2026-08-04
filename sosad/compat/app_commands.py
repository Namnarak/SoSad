"""The commonly used ``discord.app_commands`` compatibility surface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class locale_str:  # noqa: N801
    """A translatable string wrapper matching discord.py's API."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.message = message
        self.extras = kwargs
        self.args = args

    def __str__(self) -> str:
        return self.message


class TranslationContext:
    """Context passed to an app-command translator."""

    def __init__(self, *, data: Any = None, **kwargs: Any) -> None:
        self.data = data
        self.__dict__.update(kwargs)


class Translator:
    """Base translator with discord.py-compatible lifecycle hooks."""

    async def load(self) -> None:
        return None

    async def unload(self) -> None:
        return None

    async def translate(
        self,
        string: locale_str,
        locale: Any,
        context: TranslationContext,
    ) -> str | None:
        del string, locale, context
        return None


class Choice:
    """A choice option for a slash-command parameter."""

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value}

    def __repr__(self) -> str:
        return f"Choice(name={self.name!r}, value={self.value!r})"


class ContextMenu:
    """A user/message context-menu command."""

    def __init__(self, *, name: str, callback: Callable[..., Any]) -> None:
        self.name = name
        self.callback = callback
        self.description = name
        self.type = "context_menu"


def autocomplete(**kwargs: Callable[..., Any]) -> Callable[[Any], Any]:
    """Attach parameter autocomplete callbacks to a command callback."""

    def decorator(target: Any) -> Any:
        target._sosad_autocomplete = dict(kwargs)
        return target

    return decorator


class CommandTree:
    """In-memory command tree with SoSad sync delegation."""

    def __init__(self, bot: Any) -> None:
        self.client = bot
        self._global: dict[str, Any] = {}
        self._guild_commands: dict[int, dict[str, Any]] = {}
        self.translator: Translator | None = None

    async def set_translator(self, translator: Translator | None) -> None:
        if self.translator is not None:
            await self.translator.unload()
        self.translator = translator
        if translator is not None:
            await translator.load()

    @property
    def commands(self) -> list[Any]:
        return list(self._global.values())

    def add_command(
        self,
        command: Any,
        *,
        guild: Any = None,
        override: bool = False,
    ) -> Any:
        target = self._target(guild)
        if command.name in target and not override:
            raise ValueError(f"Command {command.name!r} is already registered")
        target[command.name] = command
        self.client._register_app_command(command, guild=guild)
        return command

    def remove_command(
        self,
        name: str,
        *,
        guild: Any = None,
        type: Any = None,
    ) -> Any | None:
        del type
        return self._target(guild).pop(name, None)

    def clear_commands(self, *, guild: Any = None) -> None:
        self._target(guild).clear()

    def get_commands(self, *, guild: Any = None) -> list[Any]:
        return list(self._target(guild).values())

    def copy_global_to(self, *, guild: Any) -> None:
        self._guild_commands[int(getattr(guild, "id", guild))] = dict(self._global)

    async def sync(self, *, guild: Any = None) -> list[Any]:
        await self.client._sync_tree(guild=guild)
        return self.get_commands(guild=guild)

    def command(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        guilds: Any = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Any]:
        def decorator(callback: Callable[..., Any]) -> Any:
            from sosad.compat.ext.commands import Command

            command = Command(
                callback,
                name=name,
                description=description,
                kind="slash",
                **kwargs,
            )
            command.is_app_command = True
            command.guilds = guilds
            self.add_command(command)
            return command

        return decorator

    def _target(self, guild: Any) -> dict[str, Any]:
        if guild is None:
            return self._global
        return self._guild_commands.setdefault(int(getattr(guild, "id", guild)), {})


def command(
    name: str | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Any]:
    """Create a slash command object for later ``tree.add_command`` use."""
    def decorator(func: Callable[..., Any]) -> Any:
        from sosad.compat.ext.commands import Command

        command = Command(
            func,
            name=name,
            description=description,
            kind="slash",
            **kwargs,
        )
        command.is_app_command = True
        return command

    return decorator


def _set_metadata(name: str, values: Any) -> Callable[[Any], Any]:
    def decorator(target: Any) -> Any:
        setattr(target, name, values)
        return target

    return decorator


def describe(**kwargs: str) -> Callable[[Any], Any]:
    return _set_metadata("_sosad_descriptions", kwargs)


def choices(**kwargs: list[Choice]) -> Callable[[Any], Any]:
    return _set_metadata(
        "_sosad_choices",
        {name: [choice.to_dict() for choice in values] for name, values in kwargs.items()},
    )


def rename(**kwargs: str) -> Callable[[Any], Any]:
    return _set_metadata("_sosad_renames", kwargs)


def guild_only() -> Callable[[Any], Any]:
    return _set_metadata("_sosad_guild_only", True)


__all__ = [
    "Choice",
    "CommandTree",
    "ContextMenu",
    "autocomplete",
    "choices",
    "command",
    "describe",
    "guild_only",
    "locale_str",
    "rename",
    "TranslationContext",
    "Translator",
]
