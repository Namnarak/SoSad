"""Tests for the task scheduler."""

import asyncio

import pytest

from sosad.tasks.base import TaskMeta
from sosad.tasks.decorators import loop, task
from sosad.tasks.scheduler import TaskScheduler


def test_task_decorator():
    @task(interval=60, name="my_task")
    async def my_task(): ...

    assert isinstance(my_task, TaskMeta)
    assert my_task.name == "my_task"
    assert my_task.interval == 60
    assert my_task.once is False


def test_task_decorator_once():
    @task(interval=10, once=True)
    async def my_task(): ...

    assert my_task.once is True


def test_loop_decorator():
    @loop(interval=30, name="cleanup")
    async def cleanup(): ...

    assert isinstance(cleanup, TaskMeta)
    assert cleanup.name == "cleanup"
    assert cleanup.interval == 30


def test_task_decorator_default_name():
    @task(interval=5)
    async def my_background_job(): ...

    assert my_background_job.name == "my_background_job"


def test_scheduler_register():
    scheduler = TaskScheduler()
    meta = TaskMeta(name="test", handler=lambda: None, interval=10)
    scheduler.register(meta)
    assert scheduler.registered_count == 1


def test_scheduler_unregister():
    scheduler = TaskScheduler()
    meta = TaskMeta(name="test", handler=lambda: None, interval=10)
    scheduler.register(meta)
    scheduler.unregister("test")
    assert scheduler.registered_count == 0


@pytest.mark.asyncio
async def test_scheduler_start_stop():
    call_count = 0

    async def counter():
        nonlocal call_count
        call_count += 1

    scheduler = TaskScheduler()
    meta = TaskMeta(name="counter", handler=counter, interval=0.1, autostart=False)
    scheduler.register(meta)

    running = scheduler.start("counter")
    assert running is not None
    assert running.is_running

    await asyncio.sleep(0.3)
    scheduler.stop("counter")
    assert call_count >= 1


@pytest.mark.asyncio
async def test_scheduler_run_once():
    call_count = 0

    async def counter():
        nonlocal call_count
        call_count += 1

    scheduler = TaskScheduler()
    meta = TaskMeta(name="once", handler=counter, interval=1, once=True, delay=0)
    scheduler.register(meta)

    scheduler.start("once")
    await asyncio.sleep(0.2)
    assert call_count == 1
    assert scheduler.get_running("once") is None


@pytest.mark.asyncio
async def test_scheduler_error_handler():
    error_handled = False

    async def failing_task():
        raise ValueError("boom")

    async def on_error():
        nonlocal error_handled
        error_handled = True

    scheduler = TaskScheduler()
    meta = TaskMeta(
        name="failing",
        handler=failing_task,
        interval=0.1,
        once=True,
        error_handler=on_error,
    )
    scheduler.register(meta)
    scheduler.start("failing")
    await asyncio.sleep(0.3)
    assert error_handled is True


@pytest.mark.asyncio
async def test_scheduler_stop_all():
    call_count = 0

    async def counter():
        nonlocal call_count
        call_count += 1

    scheduler = TaskScheduler()
    scheduler.register(TaskMeta(name="a", handler=counter, interval=0.1))
    scheduler.register(TaskMeta(name="b", handler=counter, interval=0.1))
    scheduler.start_all()
    assert scheduler.running_count == 2
    await asyncio.sleep(0.2)
    scheduler.stop_all()
    assert scheduler.running_count == 0


@pytest.mark.asyncio
async def test_scheduler_start_nonexistent():
    scheduler = TaskScheduler()
    result = scheduler.start("nonexistent")
    assert result is None


def test_scheduler_registered_count():
    scheduler = TaskScheduler()
    scheduler.register(TaskMeta(name="a", handler=lambda: None, interval=1))
    scheduler.register(TaskMeta(name="b", handler=lambda: None, interval=1))
    assert scheduler.registered_count == 2
