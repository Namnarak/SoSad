"""Tests for the middleware pipeline."""

import pytest
from sosad.middleware.registry import MiddlewareStack
from sosad.di.scopes import ScopeManager


@pytest.mark.asyncio
async def test_middleware_stack_builds_chain():
    """Middleware should wrap the handler in order."""
    call_order = []

    async def handler(ctx, scope):
        call_order.append("handler")

    async def mw_a(ctx, next_fn, scope):
        call_order.append("a_before")
        await next_fn(ctx, scope)
        call_order.append("a_after")

    async def mw_b(ctx, next_fn, scope):
        call_order.append("b_before")
        await next_fn(ctx, scope)
        call_order.append("b_after")

    stack = MiddlewareStack()
    stack.add(mw_a)
    stack.add(mw_b)
    stack.set_handler(handler)

    composed = stack.build()
    await composed(None, None)

    assert call_order == ["a_before", "b_before", "handler", "b_after", "a_after"]


@pytest.mark.asyncio
async def test_middleware_can_short_circuit():
    """Middleware can skip the handler by not calling next."""
    call_order = []

    async def handler(ctx, scope):
        call_order.append("handler")

    async def blocker(ctx, next_fn, scope):
        call_order.append("blocked")

    stack = MiddlewareStack()
    stack.add(blocker)
    stack.set_handler(handler)

    composed = stack.build()
    await composed(None, None)

    assert call_order == ["blocked"]
    assert "handler" not in call_order


def test_stack_no_handler_raises():
    """Building without a handler should raise."""
    stack = MiddlewareStack()
    with pytest.raises(RuntimeError, match="No final handler set"):
        stack.build()


def test_stack_clear():
    """Clearing should remove everything."""
    stack = MiddlewareStack()
    stack.add(lambda ctx, n, s: None)
    stack.set_handler(lambda ctx, s: None)
    stack.clear()
    with pytest.raises(RuntimeError):
        stack.build()


@pytest.mark.asyncio
async def test_middleware_modifies_scope():
    """Middleware can add scoped values visible to handler."""
    scope = ScopeManager()

    async def injector(ctx, next_fn, sc):
        sc.set(str, "injected_value")
        await next_fn(ctx, sc)

    async def handler(ctx, sc):
        sc.set(int, sc.resolve(str))  # pass value through

    stack = MiddlewareStack()
    stack.add(injector)
    stack.set_handler(handler)

    composed = stack.build()
    await composed(None, scope)
    assert scope.resolve(str) == "injected_value"
    assert scope.resolve(int) == "injected_value"


@pytest.mark.asyncio
async def test_middleware_error_propagation():
    """Errors in handler should propagate through middleware."""
    async def failing_handler(ctx, scope):
        raise ValueError("boom")

    async def catcher(ctx, next_fn, scope):
        try:
            await next_fn(ctx, scope)
        except ValueError as e:
            scope.set(str, f"caught: {e}")

    scope = ScopeManager()
    stack = MiddlewareStack()
    stack.add(catcher)
    stack.set_handler(failing_handler)

    composed = stack.build()
    await composed(None, scope)
    assert scope.resolve(str) == "caught: boom"
