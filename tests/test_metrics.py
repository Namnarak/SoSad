"""Tests for metrics middleware."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from sosad.middleware.metrics import get_metrics, request_metrics, reset_metrics


class TestMetricsMiddleware:
    def test_reset_metrics(self):
        reset_metrics()
        metrics = get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["command_timings"] == {}

    def test_successful_request(self):
        reset_metrics()

        mock_ctx = MagicMock()
        mock_ctx.interaction.command_name = "ping"

        async def next_fn(ctx, scope):
            pass

        import asyncio
        asyncio.run(request_metrics(mock_ctx, next_fn, None))

        metrics = get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["total_errors"] == 0
        assert "ping" in metrics["command_timings"]

    def test_failed_request(self):
        reset_metrics()

        mock_ctx = MagicMock()
        mock_ctx.interaction.command_name = "fail"

        async def next_fn(ctx, scope):
            raise ValueError("test error")

        import asyncio
        with pytest.raises(ValueError):
            asyncio.run(request_metrics(mock_ctx, next_fn, None))

        metrics = get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["total_errors"] == 1
        assert "fail" in metrics["command_timings"]

    def test_multiple_requests(self):
        reset_metrics()

        for name in ["a", "b", "a"]:
            mock_ctx = MagicMock()
            mock_ctx.interaction.command_name = name

            async def next_fn(ctx, scope):
                pass

            import asyncio
            asyncio.run(request_metrics(mock_ctx, next_fn, None))

        metrics = get_metrics()
        assert metrics["total_requests"] == 3
        assert len(metrics["command_timings"]["a"]) == 2
        assert len(metrics["command_timings"]["b"]) == 1

    def test_timing_recorded(self):
        reset_metrics()

        mock_ctx = MagicMock()
        mock_ctx.interaction.command_name = "slow"

        async def next_fn(ctx, scope):
            import time
            time.sleep(0.01)  # 10ms

        import asyncio
        asyncio.run(request_metrics(mock_ctx, next_fn, None))

        metrics = get_metrics()
        timing = metrics["command_timings"]["slow"][0]
        assert timing > 0.005  # At least 5ms
        assert timing < 0.05   # Less than 50ms

    def test_unknown_command_name(self):
        reset_metrics()

        mock_ctx = MagicMock()
        mock_ctx.interaction.command_name = None

        async def next_fn(ctx, scope):
            pass

        import asyncio
        asyncio.run(request_metrics(mock_ctx, next_fn, None))

        metrics = get_metrics()
        assert metrics["total_requests"] == 1
        assert "unknown" in metrics["command_timings"]

    def test_timing_buffer_limit(self):
        reset_metrics()

        mock_ctx = MagicMock()
        mock_ctx.interaction.command_name = "frequent"

        async def next_fn(ctx, scope):
            pass

        import asyncio
        # Fill beyond buffer limit
        for _ in range(150):
            asyncio.run(request_metrics(mock_ctx, next_fn, None))

        metrics = get_metrics()
        assert len(metrics["command_timings"]["frequent"]) == 100  # Max 100
