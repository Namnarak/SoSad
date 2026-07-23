"""Performance benchmark suite.

Measures:
    - Command registration speed
    - Context creation overhead
    - Middleware pipeline latency
    - DI container resolution speed
    - Component handler dispatch

Run:
    uv run python -m benchmarks.run
"""

from __future__ import annotations

import time
from statistics import mean, median, stdev


def bench(name: str, runs: int, fn):
    """Run benchmark and print results."""
    # Warmup
    for _ in range(100):
        fn()

    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        fn()
        elapsed = time.perf_counter_ns() - start
        times.append(elapsed / 1_000_000)  # Convert to ms

    avg = mean(times)
    med = median(times)
    hi = max(times)
    lo = min(times)
    dev = stdev(times) if len(times) > 1 else 0

    print(
        f"  {name:40s}  avg={avg:8.3f}ms  med={med:8.3f}ms  min={lo:8.3f}ms "
        f"max={hi:8.3f}ms  σ={dev:6.3f}ms"
    )


def bench_command_registry():
    from sosad.commands.registry import CommandRegistry

    reg = CommandRegistry()

    for i in range(1000):
        reg.add(f"cmd_{i}", lambda ctx: None, {})

    # Now measure lookups
    def lookup():
        reg.resolve("cmd_500")

    bench("CommandRegistry.resolve (1000 cmds)", 5000, lookup)


def bench_middleware_pipeline():
    import sosad
    from sosad.middleware.registry import MiddlewareStack

    stack = MiddlewareStack()

    async def noop_mw(ctx, next_fn, scope):
        await next_fn(ctx, scope)

    for _ in range(10):
        stack.add(noop_mw)

    async def handler(ctx, scope):
        pass

    async def run_pipeline():
        ctx = sosad.InteractionContext.__new__(sosad.InteractionContext)
        await stack.execute(ctx, handler, None)

    bench("Middleware pipeline (10 middleware)", 2000, lambda: asyncio.run(run_pipeline()))


def bench_di_resolution():
    from sosad.di import Container

    container = Container()

    class ServiceA:
        pass

    class ServiceB:
        def __init__(self, a: ServiceA):
            self.a = a

    container.register(ServiceA, singleton=True)
    container.register(ServiceB, scoped=True)

    def resolve():
        container.resolve(ServiceA)

    bench("DI resolve singleton", 10000, resolve)


def bench_embed_creation():
    from sosad.compat import Embed

    def create_embed():
        embed = Embed(title="Hello", description="World")
        embed.add_field(name="Field 1", value="Value 1")
        embed.add_field(name="Field 2", value="Value 2")
        embed.set_footer(text="Footer")
        embed.set_author(name="Author")
        return embed

    bench("Embed creation + fields", 10000, create_embed)


def bench_paginator_creation():
    from sosad.components import Paginator

    @Paginator.register("bench_pages")
    class BenchPaginator(Paginator):
        def __init__(self):
            super().__init__(pages=[{"n": i} for i in range(50)])

        async def render_page(self, page):
            return None

    def create():
        return BenchPaginator()

    bench("Paginator creation (50 pages)", 5000, create)


def bench_view_storage():
    import asyncio

    from sosad.components.storage import InMemoryViewStorage

    storage = InMemoryViewStorage()

    async def save_load():
        await storage.save("test", {"a": 1, "b": 2})
        await storage.load("test")
        await storage.delete("test")

    bench("ViewStorage save/load/delete", 5000, lambda: asyncio.run(save_load()))


def bench_task_registry():
    from sosad.tasks import TaskRegistry

    reg = TaskRegistry()

    for i in range(100):
        reg.add(
            "task_" + str(i),
            lambda: None,
            seconds=60,
        )

    bench("TaskRegistry iteration (100 tasks)", 10000, lambda: list(reg))


def bench_check_evaluation():
    from sosad import check

    async def is_admin(ctx):
        return True

    admin_check = check("admin", is_admin)

    ctx = type("FakeCtx", (), {"author": type("FakeUser", (), {"id": 123})()})()

    async def evaluate():
        await admin_check.fn(ctx)

    bench("Check evaluation", 10000, lambda: asyncio.run(evaluate()))


if __name__ == "__main__":
    import asyncio

    print("=" * 80)
    print("SoSad Performance Benchmarks")
    print("=" * 80)
    print()

    print("1. Command Registry")
    bench_command_registry()
    print()

    print("2. Middleware Pipeline")
    bench_middleware_pipeline()
    print()

    print("3. DI Container")
    bench_di_resolution()
    print()

    print("4. Embed Creation")
    bench_embed_creation()
    print()

    print("5. Paginator")
    bench_paginator_creation()
    print()

    print("6. View Storage")
    bench_view_storage()
    print()

    print("7. Task Registry")
    bench_task_registry()
    print()

    print("8. Check Evaluation")
    bench_check_evaluation()
    print()

    print("=" * 80)
    print("Done!")
