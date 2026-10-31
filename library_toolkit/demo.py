"""Real stdio MCP round trip without a model or an API key."""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from agents.mcp import MCPServerStdio

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {"search_catalog", "save_reading_item", "plan_reading"}


async def demonstrate():
    with tempfile.TemporaryDirectory(prefix="campusreads-") as scratch:
        db = Path(scratch) / "demo.sqlite3"
        async with MCPServerStdio(
            name="CampusReads protocol demo",
            params={"command": sys.executable, "args": ["-m", "library_toolkit.server"],
                    "cwd": str(ROOT), "env": {**os.environ, "LIBRARY_DB_PATH": str(db)}},
            client_session_timeout_seconds=30,
        ) as server:
            tools = await server.list_tools()
            assert {t.name for t in tools} == EXPECTED
            print("DISCOVERED EXACTLY THREE TOOLS: " + ", ".join(t.name for t in tools))
            scenarios = [
                ("search_catalog", {"query": "agents"}, False),
                ("save_reading_item", {"book_id": "B001", "list_name": "demo"}, False),
                ("plan_reading", {"query": "machine learning", "list_name": "demo"}, False),
                ("plan_reading", {"query": "machine learning", "list_name": "demo"}, False),
                ("search_catalog", {"query": "   "}, True),
                ("save_reading_item", {"book_id": "B999", "list_name": "demo"}, True),
                ("plan_reading", {"query": "underwater basket weaving", "list_name": "demo"}, True),
            ]
            for name, arguments, expect_error in scenarios:
                print(f"\nCLIENT -> SERVER: {name} {json.dumps(arguments)}")
                result = await server.call_tool(name, arguments)
                print("SERVER -> CLIENT: " + result.model_dump_json(exclude_none=True))
                assert bool(result.is_error) == expect_error
                if name == "search_catalog" and not expect_error:
                    assert not db.exists(), "Data lookup must not create storage"
            with closing(sqlite3.connect(db)) as connection:
                rows = connection.execute("SELECT list_name, book_id FROM reading_items ORDER BY book_id").fetchall()
            assert rows == [("demo", "B001"), ("demo", "B004")]
            print(f"\nPERSISTENCE VERIFIED: {rows}")
            print("PASS: discovery, all three tools, duplicate safety, and all three failure cases.")
            print("This is a protocol demonstration, not an LLM-selected agent run. Use agent --demo for that.")


if __name__ == "__main__":
    asyncio.run(demonstrate())
