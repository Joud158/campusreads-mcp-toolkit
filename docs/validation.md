# Validation record

Validated on 31 October 2026 with Python 3.11 on Windows, using the project's virtual environment.

| Check | Actual result |
|---|---|
| `python -m pytest -q` | **13 passed**, no warnings |
| `python -m library_toolkit.demo` | **Exit 0**; exactly three tools discovered; successful Data, Action, and Orchestration calls; all three expected failure results; duplicate protection and persisted rows verified |
| `python -m pip check` | **No broken requirements found** |
| Reading summary length | **371 words** in the body after rendering Markdown link labels; within 300–400 |
| Missing API key behavior | Live host exits with a clear setup message before attempting API access |

The integration test in `tests/test_agent_integration.py` runs the actual `Agent` and `Runner` against `VisibleMCPServer`, which launches a real FastMCP subprocess. A scripted model returns tool calls for all three capabilities and an unknown-book request; its next turn verifies that four real results returned through the SDK. This also exercises the request/response logging used by the live host. It is an integration test, **not evidence of natural-language routing by an OpenAI model**.

The other tests verify read-only lookup, input validation, unavailable catalog/storage errors, persistence across service instances, stable timestamps on retries, composition order, unchanged storage after a failed workflow, typed MCP schemas, annotations, and MCP error results.

The protocol demo output is saved in [protocol-demo-output.txt](protocol-demo-output.txt). It was captured from a real run, with stdout and server stderr separated. During verification, Windows exposed an open SQLite connection during temporary-directory cleanup; connections now close explicitly as well as committing or rolling back their transactions, and the complete demo exits successfully.

**Live agent validation:** the student's subsequent terminal transcript confirms a completed OpenAI agent demo. Discovery returned exactly the three tools. The model called `search_catalog` for agents, saved B001, used `plan_reading` to save B004, received `already_saved` with the original timestamp on repetition, and reported `NO_MATCHES` and `BOOK_NOT_FOUND` for the two failing requests. This supplements the automated integration checks with an actual live model run.

**Still requires student completion:** record and upload the 5–7 minute screencast and add its URL to the submission. The source repository is [campusreads-mcp-toolkit](https://github.com/Joud158/campusreads-mcp-toolkit). Use `docs/screencast.md` and `docs/submission.md` to finish the submission.
