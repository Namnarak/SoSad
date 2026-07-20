"""Tests for Persistent Views, Paginator, and Storage backends."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import hikari
import pytest

from sosad.components import Paginator, PersistentView
from sosad.components.storage import (
    FileViewStorage,
    InMemoryViewStorage,
    get_view_storage,
    set_view_storage,
)


class TestPersistentView:
    def test_create(self):
        view = PersistentView(timeout=60)
        assert view.timeout == 60
        assert view.id is not None

    def test_add_button(self):
        view = PersistentView(timeout=30)
        view.button(custom_id="btn", label="Click", style=hikari.ButtonStyle.PRIMARY)
        assert len(view._components) == 1

    def test_add_select(self):
        view = PersistentView(timeout=30)
        view.select(custom_id="sel", placeholder="Choose")
        assert len(view._components) == 1

    def test_on_click_decorator(self):
        view = PersistentView(timeout=30)
        view.button(custom_id="btn", label="Click", style=hikari.ButtonStyle.PRIMARY)

        @view.on_click("btn")
        async def handler(ctx):
            pass

        assert "btn" in view._handlers

    def test_is_expired(self):
        view = PersistentView(timeout=0.01)
        import time
        time.sleep(0.02)
        assert view.is_expired()

    def test_not_expired(self):
        view = PersistentView(timeout=3600)
        assert not view.is_expired()

    def test_parse_custom_id(self):
        view = PersistentView(timeout=60)
        encoded = view._encode_id("my_btn")
        assert encoded.startswith("sv:")
        assert encoded.endswith(":my_btn")

        parts = PersistentView.parse_custom_id(encoded)
        assert parts is not None
        assert parts[0] == view.id
        assert parts[1] == "my_btn"

    def test_decode_id(self):
        view = PersistentView(timeout=60)
        encoded = view._encode_id("test")
        decoded = view._decode_id(encoded)
        assert decoded == "test"

    def test_decode_id_no_prefix(self):
        decoded = PersistentView._decode_id("plain_id")
        assert decoded == "plain_id"

    def test_get_view(self):
        view = PersistentView(timeout=60)
        found = PersistentView.get_view(view.id)
        assert found is view

    def test_get_view_nonexistent(self):
        assert PersistentView.get_view("nonexistent") is None

    def test_cleanup_expired(self):
        import time
        view = PersistentView(timeout=0.01)
        time.sleep(0.02)
        PersistentView.cleanup_expired()
        assert PersistentView.get_view(view.id) is None

    def test_on_timeout(self):
        calls = []

        class TestView(PersistentView):
            async def on_timeout(self):
                calls.append("timeout")

        view = TestView(timeout=0.01)
        import time
        time.sleep(0.02)
        PersistentView.cleanup_expired()
        assert "timeout" in calls

    def test_get_handlers(self):
        view = PersistentView(timeout=60)
        view.button(custom_id="btn", label="Click", style=hikari.ButtonStyle.PRIMARY)

        async def handler(ctx):
            pass

        view.set_handler("btn", handler)
        handlers = view.get_handlers()
        assert len(handlers) == 1

    def test_build_rows(self):
        view = PersistentView(timeout=60)
        view.button(custom_id="a", label="A", style=hikari.ButtonStyle.PRIMARY)
        view.button(custom_id="b", label="B", style=hikari.ButtonStyle.SECONDARY)
        rows = view.build_rows()
        assert len(rows) >= 1

    def test_views_class_variable(self):
        count_before = len(PersistentView.views)
        view = PersistentView(timeout=60)
        assert len(PersistentView.views) == count_before + 1
        assert PersistentView.views[view.id] is view


class TestPaginator:
    def test_create(self):
        pages = [{"page": 1}, {"page": 2}]
        paginator = Paginator(pages=pages)

        assert paginator.total_pages == 2
        assert paginator._current_page == 0
        assert paginator.current_page_data == {"page": 1}

    def test_next_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(3)])
        paginator.next_page()
        assert paginator._current_page == 1
        assert paginator.current_page_data == {"n": 1}

    def test_previous_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(3)])
        paginator._current_page = 2
        paginator.previous_page()
        assert paginator._current_page == 1

    def test_first_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(5)])
        paginator._current_page = 3
        paginator.first_page()
        assert paginator._current_page == 0

    def test_last_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(5)])
        paginator.last_page()
        assert paginator._current_page == 4

    def test_is_first_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(3)])
        assert paginator.is_first_page
        paginator.next_page()
        assert not paginator.is_first_page

    def test_is_last_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(3)])
        assert not paginator.is_last_page
        paginator.last_page()
        assert paginator.is_last_page

    def test_go_to_page(self):
        paginator = Paginator(pages=[{"n": i} for i in range(10)])
        paginator.go_to_page(5)
        assert paginator._current_page == 5

    def test_go_to_page_clamps_low(self):
        paginator = Paginator(pages=[{"n": i} for i in range(10)])
        paginator.go_to_page(-5)
        assert paginator._current_page == 0

    def test_go_to_page_clamps_high(self):
        paginator = Paginator(pages=[{"n": i} for i in range(10)])
        paginator.go_to_page(100)
        assert paginator._current_page == 9

    def test_single_page(self):
        paginator = Paginator(pages=[{"only": "page"}])
        assert paginator.total_pages == 1

    def test_page_range_default(self):
        paginator = Paginator(pages=[{"n": i} for i in range(20)], page_range_size=5)
        assert paginator.page_range == (0, 4)
        paginator.go_to_page(10)
        assert paginator.page_range == (10, 14)
        paginator.go_to_page(19)
        assert paginator.page_range == (15, 19)


class TestViewStorage:
    def test_in_memory_storage(self):
        storage = InMemoryViewStorage()

        async def _test():
            await storage.save("test", {"foo": "bar"})
            data = await storage.load("test")
            assert data == {"foo": "bar"}
            assert await storage.load("nonexistent") is None
            await storage.delete("test")
            assert await storage.load("test") is None

        import asyncio
        asyncio.run(_test())

    def test_in_memory_expiry(self):
        storage = InMemoryViewStorage()

        async def _test():
            import time
            await storage.save("old", {"created_at": time.time() - 100})
            await storage.save("new", {"created_at": time.time()})
            count = await storage.cleanup_expired(timeout=50)
            assert count == 1
            assert await storage.load("old") is None
            assert await storage.load("new") is not None

        import asyncio
        asyncio.run(_test())

    def test_file_storage(self, tmp_path):
        storage = FileViewStorage(str(tmp_path / "views"))

        async def _test():
            await storage.save("test", {"value": 42})
            data = await storage.load("test")
            assert data == {"value": 42}
            assert (tmp_path / "views" / "test.json").exists()
            await storage.delete("test")
            assert await storage.load("test") is None

        import asyncio
        asyncio.run(_test())

    def test_file_storage_expiry(self, tmp_path):
        storage = FileViewStorage(str(tmp_path / "views2"))

        async def _test():
            import time
            await storage.save("old", {"created_at": time.time() - 100})
            await storage.save("new", {"created_at": time.time()})
            count = await storage.cleanup_expired(timeout=50)
            assert count == 1

        import asyncio
        asyncio.run(_test())

    def test_set_and_get_storage(self):
        prev = get_view_storage()
        new_storage = InMemoryViewStorage()
        set_view_storage(new_storage)
        assert get_view_storage() is new_storage
        set_view_storage(prev)
