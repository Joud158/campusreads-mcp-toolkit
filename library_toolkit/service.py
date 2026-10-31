"""Deterministic library operations shared by the three MCP entry points."""

import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class LibraryError(ValueError):
    """An expected, user-correctable tool failure."""


class Book(BaseModel):
    book_id: str
    title: str
    author: str
    topics: list[str]


class SearchResult(BaseModel):
    query: str
    total_matches: int
    books: list[Book]


class SaveResult(BaseModel):
    status: Literal["created", "already_saved"]
    list_name: str
    book: Book
    saved_at: str


class PlanResult(BaseModel):
    query: str
    selection_rule: str
    steps: list[str]
    saved: SaveResult


CATALOG_PATH = Path(__file__).with_name("catalog.json")


def clean_text(value: str, name: str, maximum: int = 120) -> str:
    value = value.strip()
    if not value or len(value) > maximum:
        raise LibraryError(f"INVALID_INPUT: {name} must contain 1-{maximum} characters after trimming.")
    return value


class LibraryService:
    def __init__(self, db_path: Path, catalog_path: Path = CATALOG_PATH):
        self.db_path = db_path
        self.catalog_path = catalog_path

    def _catalog(self) -> list[Book]:
        try:
            return [Book.model_validate(item) for item in json.loads(self.catalog_path.read_text(encoding="utf-8"))]
        except (OSError, ValueError, TypeError) as exc:
            raise LibraryError("CATALOG_UNAVAILABLE: Cannot read the catalog; check the bundled catalog.json.") from exc

    def search_catalog(self, query: str, limit: int = 5) -> SearchResult:
        query = clean_text(query, "query")
        if not 1 <= limit <= 10:
            raise LibraryError("INVALID_INPUT: limit must be between 1 and 10.")
        tokens = re.findall(r"\w+", query.casefold())
        if not tokens:
            raise LibraryError("INVALID_INPUT: query must contain a letter or number.")
        matches = [b for b in self._catalog() if all(
            token in " ".join([b.book_id, b.title, b.author, *b.topics]).casefold() for token in tokens
        )]
        matches.sort(key=lambda b: (b.title.casefold(), b.book_id))
        return SearchResult(query=query, total_matches=len(matches), books=matches[:limit])

    def save_reading_item(self, book_id: str, list_name: str) -> SaveResult:
        book_id = clean_text(book_id, "book_id", 30).upper()
        list_name = clean_text(list_name, "list_name", 60).casefold()
        book = next((b for b in self._catalog() if b.book_id == book_id), None)
        if book is None:
            raise LibraryError(f"BOOK_NOT_FOUND: No catalog book has ID {book_id}; search the catalog first.")
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.db_path, timeout=5)) as connection, connection:
                connection.execute("""CREATE TABLE IF NOT EXISTS reading_items (
                    list_name TEXT NOT NULL, book_id TEXT NOT NULL, saved_at TEXT NOT NULL,
                    PRIMARY KEY (list_name, book_id))""")
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO reading_items VALUES (?, ?, ?)",
                    (list_name, book_id, datetime.now(timezone.utc).isoformat()),
                )
                created = cursor.rowcount == 1
                saved_at = connection.execute(
                    "SELECT saved_at FROM reading_items WHERE list_name = ? AND book_id = ?",
                    (list_name, book_id),
                ).fetchone()[0]
        except (OSError, sqlite3.Error) as exc:
            raise LibraryError("STORAGE_UNAVAILABLE: Cannot save the reading item; check the database path and permissions.") from exc
        return SaveResult(status="created" if created else "already_saved", list_name=list_name,
                          book=book, saved_at=saved_at)

    def plan_reading(self, query: str, list_name: str) -> PlanResult:
        # Validate the write destination before doing the lookup; no writes on lookup failure.
        list_name = clean_text(list_name, "list_name", 60)
        found = self.search_catalog(query, limit=1)
        if not found.books:
            raise LibraryError(f"NO_MATCHES: No book matches '{found.query}'; try a broader topic. Nothing was saved.")
        saved = self.save_reading_item(found.books[0].book_id, list_name)
        return PlanResult(query=found.query, selection_rule="First title alphabetically (book ID breaks ties).",
                          steps=["search_catalog", "save_reading_item"], saved=saved)
