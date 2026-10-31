import asyncio
import sqlite3
from contextlib import closing

import pytest
from fastmcp import Client

from library_toolkit.service import LibraryError, LibraryService
from library_toolkit.server import create_server


@pytest.fixture
def service(tmp_path):
    return LibraryService(tmp_path / "reading.sqlite3")


def test_data_is_read_only_and_sorted(service):
    result = service.search_catalog("AGENTS")
    assert [b.book_id for b in result.books] == ["B001", "B005"]
    assert not service.db_path.exists()
    assert service.search_catalog("agents", 1).total_matches == 2
    assert len(service.search_catalog("agents", 1).books) == 1


@pytest.mark.parametrize("query", ["", "   ", "!!!", "x" * 121])
def test_data_invalid_query(service, query):
    with pytest.raises(LibraryError, match="INVALID_INPUT"):
        service.search_catalog(query)
    assert not service.db_path.exists()


def test_data_no_matches_and_missing_catalog(service, tmp_path):
    assert service.search_catalog("nonexistent-topic").books == []
    broken = LibraryService(service.db_path, tmp_path / "missing.json")
    with pytest.raises(LibraryError, match="CATALOG_UNAVAILABLE"):
        broken.search_catalog("agents")


def test_save_persists_across_instances_and_is_idempotent(service):
    first = service.save_reading_item("b001", " Demo ")
    second = LibraryService(service.db_path).save_reading_item("B001", "demo")
    assert first.status == "created"
    assert second.status == "already_saved"
    assert first.saved_at == second.saved_at
    with closing(sqlite3.connect(service.db_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM reading_items").fetchone()[0] == 1


def test_action_unknown_book_does_not_write(service):
    with pytest.raises(LibraryError, match="BOOK_NOT_FOUND"):
        service.save_reading_item("B999", "demo")
    assert not service.db_path.exists()


def test_storage_failure_is_clear(service, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    broken = LibraryService(blocker / "db.sqlite3")
    with pytest.raises(LibraryError, match="STORAGE_UNAVAILABLE"):
        broken.save_reading_item("B001", "demo")


def test_orchestration_calls_data_then_action(service, monkeypatch):
    calls = []
    original_search = service.search_catalog
    original_save = service.save_reading_item

    def search(*args, **kwargs):
        calls.append("search_catalog")
        return original_search(*args, **kwargs)

    def save(*args, **kwargs):
        calls.append("save_reading_item")
        return original_save(*args, **kwargs)

    monkeypatch.setattr(service, "search_catalog", search)
    monkeypatch.setattr(service, "save_reading_item", save)
    result = service.plan_reading("machine learning", "demo")
    assert calls == result.steps == ["search_catalog", "save_reading_item"]
    assert result.saved.book.book_id == "B004"
    assert result.saved.status == "created"


def test_orchestration_failure_preserves_existing_state(service):
    service.save_reading_item("B001", "demo")
    before = service.db_path.read_bytes()
    with pytest.raises(LibraryError, match="NO_MATCHES"):
        service.plan_reading("underwater basket weaving", "demo")
    assert service.db_path.read_bytes() == before


def test_wire_schemas_annotations_validation_and_errors(tmp_path):
    async def scenario():
        async with Client(create_server(tmp_path / "wire.sqlite3")) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools} == {"search_catalog", "save_reading_item", "plan_reading"}
            for tool in tools:
                assert tool.description
                assert tool.input_schema["properties"]
                assert tool.output_schema
            data = next(t for t in tools if t.name == "search_catalog")
            assert data.annotations.read_only_hint is True
            assert (await client.call_tool("search_catalog", {"query": "agents"})).data.total_matches == 2
            assert (await client.call_tool("save_reading_item", {"book_id": "B001", "list_name": "demo"})).data.status == "created"
            assert (await client.call_tool("plan_reading", {"query": "machine learning", "list_name": "demo"})).data.saved.book.book_id == "B004"
            for name, args in [
                ("search_catalog", {"query": "   "}),
                ("search_catalog", {"query": "agents", "limit": 0}),
                ("save_reading_item", {"book_id": "B999", "list_name": "demo"}),
                ("plan_reading", {"query": "missingtopic", "list_name": "demo"}),
            ]:
                result = await client.call_tool(name, args, raise_on_error=False)
                assert result.is_error
    asyncio.run(scenario())
