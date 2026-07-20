"""Task scheduler — manages background task lifecycle."""

from __future__ import annotations

import asyncio
import logging

from sosad.tasks.base import RunningTask, TaskMeta

logger = logging.getLogger("sosad.tasks")


class TaskScheduler:
    """Manages background task lifecycle.

    Usage::

        scheduler = TaskScheduler()
        scheduler.register(my_task_meta)
        scheduler.start_all()
        # later...
        scheduler.stop_all()
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskMeta] = {}
        self._running: dict[str, RunningTask] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._counter = 0

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def register(self, meta: TaskMeta) -> None:
        """Register a task."""
        self._tasks[meta.name] = meta
        logger.debug("Registered task: %s (interval=%.1fs)", meta.name, meta.interval)

    def unregister(self, name: str) -> None:
        """Unregister a task."""
        self._tasks.pop(name, None)

    def start(self, name: str) -> RunningTask | None:
        """Start a specific task."""
        meta = self._tasks.get(name)
        if meta is None:
            logger.warning("Task not found: %s", name)
            return None
        return self._start_task(meta)

    def stop(self, name: str) -> None:
        """Stop a specific task."""
        running = self._running.pop(name, None)
        if running is not None:
            running.cancel()
            logger.debug("Stopped task: %s", name)

    def start_all(self) -> None:
        """Start all registered tasks that have autostart=True."""
        for meta in self._tasks.values():
            if meta.autostart:
                self._start_task(meta)

    def stop_all(self) -> None:
        """Stop all running tasks."""
        for name in list(self._running.keys()):
            self.stop(name)

    def _start_task(self, meta: TaskMeta) -> RunningTask:
        """Start a task as a background asyncio task."""
        self._counter += 1
        task_id = self._counter

        future = asyncio.ensure_future(self._run_loop(meta))

        running = RunningTask(
            meta=meta,
            task_id=task_id,
            _future=future,
        )
        self._running[meta.name] = running
        logger.info("Started task: %s (id=%d)", meta.name, task_id)
        return running

    async def _run_loop(self, meta: TaskMeta) -> None:
        """Run a task in a loop."""
        if meta.delay > 0:
            await asyncio.sleep(meta.delay)

        while True:
            try:
                await meta.handler()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in task: %s", meta.name)
                if meta.error_handler is not None:
                    try:
                        await meta.error_handler()
                    except Exception:
                        logger.exception("Error in task error handler: %s", meta.name)

            if meta.once:
                break

            try:
                await asyncio.sleep(meta.interval)
            except asyncio.CancelledError:
                break

        self._running.pop(meta.name, None)
        logger.debug("Task finished: %s", meta.name)

    @property
    def running_count(self) -> int:
        return len(self._running)

    @property
    def registered_count(self) -> int:
        return len(self._tasks)

    def get_running(self, name: str) -> RunningTask | None:
        return self._running.get(name)


__all__ = ["TaskScheduler"]
