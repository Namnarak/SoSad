"""A practical discord.ext.commands compatibility surface.

The implementation stores discord.py-style command metadata and translates
it into SoSad's interaction command registry when a cog is attached to a Bot.
It intentionally keeps the public decorator and object shapes familiar so
existing cogs can be imported and migrated incrementally.
"""

from __future__ import annotations

import functools
import inspect
import time
from enum import Enum
from typing import Any

from sosad.compat.bot import Bot as Bot
from sosad.compat.context import Context as Context


class CommandError(Exception):
    """Base class for command errors."""


class BadArgument(CommandError):
    """Raised when a command argument cannot be converted."""


class CommandNotFound(CommandError):
    """Raised when a prefix command cannot be resolved."""


class RangeError(BadArgument):
    """Raised when a value falls outside a declared command range."""


class MissingRequiredAttachment(BadArgument):
    """Raised when a required attachment argument is absent."""


class CommandOnCooldown(CommandError):
    def __init__(self, retry_after: float = 0.0) -> None:
        self.retry_after = retry_after
        super().__init__(f"You are on cooldown. Try again in {retry_after:.2f}s.")


class NotOwner(CommandError):
    """Raised when an owner-only command is used by another user."""


class MissingPermissions(CommandError):
    def __init__(self, missing_permissions: list[str] | tuple[str, ...] = ()) -> None:
        self.missing_permissions = list(missing_permissions)
        super().__init__(", ".join(self.missing_permissions))


class BotMissingPermissions(MissingPermissions):
    """Raised when the bot lacks a required permission."""


class MissingRequiredArgument(BadArgument):
    def __init__(self, param: Any = None) -> None:
        self.param = param
        super().__init__(f"Missing required argument: {getattr(param, 'name', param)}")


class DisabledCommand(CommandError):
    """Raised when a command has been disabled."""


class ExtensionAlreadyLoaded(CommandError):
    """Raised when an extension is loaded twice."""


class ExtensionNotLoaded(CommandError):
    """Raised when an extension is not loaded."""


class BucketType(Enum):
    DEFAULT = "default"
    USER = "user"
    MEMBER = "member"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"

    # discord.py uses lowercase enum members in user code.
    default = DEFAULT
    user = USER
    member = MEMBER
    guild = GUILD
    channel = CHANNEL
    role = ROLE


class Range:
    """Annotation marker for bounded slash-command values."""

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        if isinstance(item, tuple) and item:
            return item[0]
        return item


class Cooldown:
    """Small discord.py-compatible cooldown bucket."""

    def __init__(self, rate: int, per: float) -> None:
        self.rate = rate
        self.per = per
        self._window = 0.0
        self._tokens = rate

    def copy(self) -> Cooldown:
        return Cooldown(self.rate, self.per)

    def get_tokens(self, current: float) -> int:
        if current > self._window + self.per:
            self._tokens = self.rate
            self._window = current
        return self._tokens

    def get_retry_after(self, current: float) -> float:
        return max(self._window + self.per - current, 0.0)

    def update_rate_limit(self, current: float | None = None) -> float | None:
        current = time.monotonic() if current is None else current
        self.get_tokens(current)
        if self._tokens <= 0:
            return self.get_retry_after(current)
        self._tokens -= 1
        return None


class CooldownMapping:
    """Minimal mapping used by button and command cooldowns."""

    def __init__(self, cooldown: Cooldown, key: Any = None) -> None:
        self._cooldown = cooldown
        self._key = key
        self._cache: dict[Any, Cooldown] = {}

    @classmethod
    def from_cooldown(cls, rate: int, per: float, type: Any) -> CooldownMapping:
        return cls(Cooldown(rate, per), type)

    def get_bucket(self, message: Any, current: float | None = None) -> Cooldown:
        del current
        key = self._key(message) if callable(self._key) else getattr(message, "id", 0)
        try:
            return self._cache.setdefault(key, self._cooldown.copy())
        except TypeError:
            return self._cache.setdefault(repr(key), self._cooldown.copy())

    def update_rate_limit(self, message: Any, current: float | None = None) -> float | None:
        return self.get_bucket(message, current).update_rate_limit(current)


class Converter:
    """Base converter placeholder compatible with discord.py annotations."""

    async def convert(self, ctx: Any, argument: str) -> Any:
        return argument


class Greedy[T]:
    """Annotation marker for a greedy command argument."""


class _Check:
    def __init__(self, name: str, value: Any = None) -> None:
        self.name = name
        self.value = value

    def __call__(self, target: Any) -> Any:
        checks = list(getattr(target, "__sosad_compat_checks__", ()))
        checks.append(self)
        if isinstance(target, Command):
            target.checks = checks
        else:
            target.__sosad_compat_checks__ = tuple(checks)
        return target


class Command:
    """Descriptor carrying a discord.py-style command callback."""

    def __init__(
        self,
        callback: Any,
        *,
        name: str | None = None,
        description: str | None = None,
        kind: str = "prefix",
        aliases: tuple[str, ...] = (),
        parent: Group | None = None,
        **kwargs: Any,
    ) -> None:
        self.callback = callback
        self.name = name or getattr(callback, "__name__", "command")
        self.description = description or inspect.getdoc(callback) or self.name
        self.kind = kind
        self.aliases = tuple(aliases)
        self.parent = parent
        self.checks: list[Any] = list(getattr(callback, "__sosad_compat_checks__", ()))
        self.cooldown_config = getattr(callback, "__sosad_compat_cooldown__", None)
        self.dynamic_cooldown = getattr(callback, "__sosad_compat_dynamic_cooldown__", None)
        self.error_handler: Any = None
        self.before_invoke_handler: Any = None
        self.after_invoke_handler: Any = None
        self._autocomplete = dict(getattr(callback, "_sosad_autocomplete", {}))
        self.kwargs = kwargs
        functools.update_wrapper(self, callback)
        self.__wrapped__ = callback

    def __set_name__(self, owner: type, name: str) -> None:
        if self.name == "command":
            self.name = name

    def __get__(self, instance: Any, owner: type | None = None) -> Command | BoundCommand:
        if instance is None:
            return self
        return BoundCommand(self, instance)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.callback(*args, **kwargs)

    @property
    def qualified_name(self) -> str:
        if self.parent is None:
            return self.name
        return f"{self.parent.qualified_name} {self.name}"

    def error(self, handler: Any) -> Any:
        self.error_handler = handler
        return handler

    def before_invoke(self, handler: Any) -> Any:
        self.before_invoke_handler = handler
        return handler

    def after_invoke(self, handler: Any) -> Any:
        self.after_invoke_handler = handler
        return handler

    def autocomplete(self, parameter: str) -> Any:
        def decorator(callback: Any) -> Any:
            self._autocomplete[parameter] = callback
            return callback

        return decorator


class BoundCommand:
    def __init__(self, command: Command, instance: Any) -> None:
        self.command = command
        self.instance = instance
        self.callback = functools.partial(command.callback, instance)
        self.name = command.name
        self.description = command.description
        self.aliases = command.aliases

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        result = self.callback(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result


class Group(Command):
    def __init__(self, callback: Any, **kwargs: Any) -> None:
        super().__init__(callback, **kwargs)
        self.children: dict[str, Command] = {}

    def command(
        self,
        name: str | None = None,
        *,
        description: str | None = None,
        **kwargs: Any,
    ) -> Any:
        def decorator(callback: Any) -> Command:
            child = Command(
                callback,
                name=name,
                description=description,
                kind=self.kind,
                parent=self,
                **kwargs,
            )
            self.children[child.name] = child
            return child

        return decorator

    def get_commands(self) -> list[Command]:
        return list(self.children.values())


class CogMeta(type):
    def __new__(
        mcls,
        class_name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> CogMeta:
        cog_name = kwargs.pop("name", None)
        cls = super().__new__(mcls, class_name, bases, namespace, **kwargs)
        cls.__cog_name__ = cog_name or class_name.lower()
        return cls


class Cog(metaclass=CogMeta):
    """Base class for extension cogs."""

    __cog_name__: str

    def __init__(self) -> None:
        self.bot: Any = None

    def _set_bot(self, bot: Any) -> None:
        self.bot = bot

    @classmethod
    def listener(cls, name: str | None = None) -> Any:
        def decorator(func: Any) -> Any:
            func.__sosad_listener__ = name or func.__name__
            return func

        return decorator

    def get_commands(self) -> list[Command]:
        """Return commands declared directly on this cog."""
        return [
            value
            for value in vars(type(self)).values()
            if isinstance(value, Command)
        ]

    def get_app_commands(self) -> list[Command]:
        return self.get_commands()


def _factory(command_type: type[Command], **options: Any) -> Any:
    maybe_callback = options.pop("_callback", None)
    if maybe_callback is not None:
        return command_type(maybe_callback, **options)

    def decorator(callback: Any) -> Command:
        return command_type(callback, **options)

    return decorator


def command(
    name: str | Any | None = None,
    *,
    description: str | None = None,
    aliases: tuple[str, ...] = (),
    **kwargs: Any,
) -> Any:
    if callable(name):
        return Command(name, description=description, aliases=aliases, **kwargs)
    return _factory(
        Command,
        name=name,
        description=description,
        aliases=aliases,
        kind="prefix",
        **kwargs,
    )


def hybrid_command(
    name: str | None = None,
    *,
    description: str | None = None,
    aliases: tuple[str, ...] = (),
    **kwargs: Any,
) -> Any:
    return _factory(
        Command,
        name=name,
        description=description,
        aliases=aliases,
        kind="hybrid",
        **kwargs,
    )


def group(
    name: str | None = None,
    *,
    description: str | None = None,
    aliases: tuple[str, ...] = (),
    **kwargs: Any,
) -> Any:
    return _factory(
        Group,
        name=name,
        description=description,
        aliases=aliases,
        kind="prefix",
        **kwargs,
    )


def hybrid_group(
    name: str | None = None,
    *,
    description: str | None = None,
    aliases: tuple[str, ...] = (),
    **kwargs: Any,
) -> Any:
    return _factory(
        Group,
        name=name,
        description=description,
        aliases=aliases,
        kind="hybrid",
        **kwargs,
    )


def _check(name: str, **value: Any) -> Any:
    return _Check(name, value or None)


def has_permissions(**permissions: bool) -> Any:
    return _check("has_permissions", **permissions)


def bot_has_permissions(**permissions: bool) -> Any:
    return _check("bot_has_permissions", **permissions)


def has_guild_permissions(**permissions: bool) -> Any:
    return _check("has_guild_permissions", **permissions)


def has_any_role(*roles: int | str) -> Any:
    return _Check("has_any_role", roles)


def is_owner() -> Any:
    return _check("is_owner")


def guild_only() -> Any:
    return _check("guild_only")


def cooldown(rate: int, per: float, type: BucketType = BucketType.default) -> Any:
    return _Check("cooldown", (rate, per, type))


def dynamic_cooldown(factory: Any, type: BucketType = BucketType.default) -> Any:
    """Attach a callable cooldown factory to a command callback."""

    def decorator(target: Any) -> Any:
        target.__sosad_compat_dynamic_cooldown__ = (factory, type)
        return target

    return decorator


def when_mentioned_or(*prefixes: str) -> Any:
    """Return a prefix resolver compatible with discord.py."""

    def resolver(bot: Any, message: Any) -> list[str]:
        return list(prefixes)

    return resolver


class _CleanContent:
    def __init__(self, *, use_nicknames: bool = False, fix_channel_mentions: bool = True) -> None:
        self.use_nicknames = use_nicknames
        self.fix_channel_mentions = fix_channel_mentions


clean_content = _CleanContent


def cog(cls: type) -> type:
    """Convert a plain class into a :class:`Cog` subclass."""
    if not issubclass(cls, Cog):
        cls = CogMeta(cls.__name__, (Cog, *cls.__bases__), dict(cls.__dict__))
    return cls


Client = Bot
AutoShardedBot = Bot


__all__ = [
    "BadArgument",
    "AutoShardedBot",
    "Bot",
    "BotMissingPermissions",
    "BoundCommand",
    "BucketType",
    "Cog",
    "Command",
    "CommandError",
    "CommandNotFound",
    "CommandOnCooldown",
    "Context",
    "Client",
    "Converter",
    "Cooldown",
    "CooldownMapping",
    "DisabledCommand",
    "ExtensionAlreadyLoaded",
    "ExtensionNotLoaded",
    "Group",
    "Greedy",
    "MissingPermissions",
    "MissingRequiredArgument",
    "MissingRequiredAttachment",
    "NotOwner",
    "Range",
    "RangeError",
    "bot_has_permissions",
    "clean_content",
    "cog",
    "command",
    "cooldown",
    "dynamic_cooldown",
    "guild_only",
    "group",
    "has_any_role",
    "has_guild_permissions",
    "has_permissions",
    "hybrid_command",
    "hybrid_group",
    "is_owner",
    "when_mentioned_or",
]
