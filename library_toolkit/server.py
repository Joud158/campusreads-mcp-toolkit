"""Exactly three public MCP tools; stdout is reserved for MCP messages."""

import logging
import os
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from library_toolkit.service import LibraryError, LibraryService, PlanResult, SaveResult, SearchResult

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("campusreads")


def create_server(db_path: Path | None = None) -> FastMCP:
    service = LibraryService(db_path or Path(os.getenv("LIBRARY_DB_PATH", str(ROOT / "storage" / "reading_list.sqlite3"))))
    mcp = FastMCP("CampusReads")

    @mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False})
    def search_catalog(
        query: Annotated[str, Field(min_length=1, max_length=120, description="Words from a title, author, topic, or book ID; all words must match.")],
        limit: Annotated[int, Field(ge=1, le=10, description="Maximum books to return.")] = 5,
    ) -> SearchResult:
        """DATA: Search the bundled demo library catalog without changing state. Returns alphabetically sorted books and total_matches; no matches is an empty list. Blank or punctuation-only queries are errors."""
        log.info("DATA search_catalog query=%r", query)
        try:
            return service.search_catalog(query, limit)
        except LibraryError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
    def save_reading_item(
        book_id: Annotated[str, Field(min_length=1, max_length=30, description="Existing catalog ID such as B001.")],
        list_name: Annotated[str, Field(min_length=1, max_length=60, description="Reading-list name; trimmed and case-insensitive.")],
    ) -> SaveResult:
        """ACTION: Persist one known book in a local SQLite reading list. Use only when the user requests a save. Returns created or already_saved with the original timestamp. Unknown IDs or unavailable storage produce clear errors."""
        log.info("ACTION save_reading_item book_id=%r list=%r", book_id, list_name)
        try:
            return service.save_reading_item(book_id, list_name)
        except LibraryError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
    def plan_reading(
        query: Annotated[str, Field(min_length=1, max_length=120, description="Catalog search words for the requested reading topic.")],
        list_name: Annotated[str, Field(min_length=1, max_length=60, description="Destination reading-list name.")],
    ) -> PlanResult:
        """ORCHESTRATION: Fulfill a find-and-save request by calling search_catalog then save_reading_item implementations. Selects the first title alphabetically, not a subjective best book. Returns the selection rule, steps, and save receipt. NO_MATCHES causes no write. Use only when saving is requested."""
        log.info("ORCHESTRATION plan_reading query=%r list=%r", query, list_name)
        try:
            result = service.plan_reading(query, list_name)
            log.info("ORCHESTRATION completed: search_catalog -> save_reading_item (%s)", result.saved.status)
            return result
        except LibraryError as exc:
            log.info("ORCHESTRATION failed: %s", exc)
            raise ToolError(str(exc)) from exc

    return mcp


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[SERVER] %(message)s")
    create_server().run(transport="stdio", show_banner=False)
