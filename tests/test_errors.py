"""Tests for error handling pipeline."""

import asyncio
import pytest
from sosad.errors.base import CheckFailed, RateLimited, CommandNotFound, SoSadError
from sosad.errors.handler import ErrorPipeline


@pytest.mark.asyncio
async def test_error_pipeline_handler():
    """Error pipeline should dispatch to the right handler."""
    caught = []

    async def on_check(error, ctx):
        caught.append(("check", str(error)))

    pipeline = ErrorPipeline()
    pipeline.on(CheckFailed, on_check)

    await pipeline.handle(CheckFailed("not allowed"), None)
    assert len(caught) == 1
    assert caught[0] == ("check", "not allowed")


@pytest.mark.asyncio
async def test_error_pipeline_default():
    """Unmatched errors should go to default handler."""
    caught = []

    async def custom_default(error, ctx):
        caught.append(str(error))

    pipeline = ErrorPipeline()
    pipeline.set_default(custom_default)

    await pipeline.handle(RuntimeError("oops"), None)
    assert caught == ["oops"]


@pytest.mark.asyncio
async def test_error_pipeline_order():
    """Most specific handler should win."""
    caught = []

    async def on_so_sad(error, ctx):
        caught.append("sosad")

    async def on_command(error, ctx):
        caught.append("command")

    pipeline = ErrorPipeline()
    pipeline.on(SoSadError, on_so_sad)
    pipeline.on(CommandNotFound, on_command)

    # CommandNotFound is a SoSadError — first match (SoSadError) should win
    await pipeline.handle(CommandNotFound("nope"), None)
    assert caught == ["sosad"]


def test_exception_hierarchy():
    assert issubclass(CheckFailed, SoSadError)
    assert issubclass(RateLimited, SoSadError)
    assert issubclass(CommandNotFound, SoSadError)
