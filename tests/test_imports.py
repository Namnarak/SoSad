"""Test that all modules can be imported."""

import sosad


def test_version() -> None:
    """Test version is defined."""
    assert sosad.__version__ == "0.1.2"


def test_core_imports() -> None:
    """Test core imports."""
    assert sosad.Client is not None
    assert sosad.App is not None


def test_context_imports() -> None:
    """Test context imports."""
    assert sosad.InteractionContext is not None
    assert sosad.ResponseBuilder is not None


def test_command_imports() -> None:
    """Test command imports."""
    assert sosad.slash_command is not None
    assert sosad.sub_command is not None
    assert sosad.command_group is not None
    assert sosad.CommandRegistry is not None


def test_di_imports() -> None:
    """Test DI imports."""
    assert sosad.Container is not None
    assert sosad.ScopeManager is not None
    assert sosad.inject is not None


def test_middleware_imports() -> None:
    """Test middleware imports."""
    assert sosad.MiddlewareFunc is not None
    assert sosad.HandlerFunc is not None
    assert sosad.MiddlewareStack is not None


def test_event_imports() -> None:
    """Test event imports."""
    assert sosad.EventDispatcher is not None
    assert sosad.listen is not None


def test_check_imports() -> None:
    """Test check imports."""
    assert sosad.CheckResult is not None
    assert sosad.check is not None
    assert sosad.is_owner is not None
    assert sosad.has_permissions is not None


def test_cooldown_imports() -> None:
    """Test cooldown imports."""
    assert sosad.BucketScope is not None
    assert sosad.CooldownConfig is not None
    assert sosad.cooldown is not None


def test_permission_imports() -> None:
    """Test permission imports."""
    assert sosad.PermissionResolver is not None
    assert sosad.requires_permissions is not None


def test_error_imports() -> None:
    """Test error imports."""
    assert sosad.SoSadError is not None
    assert sosad.CommandError is not None
    assert sosad.CheckFailed is not None
    assert sosad.RateLimited is not None
    assert sosad.ErrorPipeline is not None


def test_plugin_imports() -> None:
    """Test plugin imports."""
    assert sosad.Plugin is not None
    assert sosad.PluginManager is not None


def test_hikari_reexport() -> None:
    """Test hikari is re-exported."""
    assert sosad.hikari is not None
    assert sosad.hikari.GatewayBot is not None
