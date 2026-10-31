# Six-minute screencast plan

This is a recording script, **not a completed recording**. Use your own voice and adapt the wording. Target 6:00 total (allowed range: 5–7 minutes). Prepare the API key in `.env` before recording; keep that file closed. Open the README, server, service, tests, and a terminal with the virtual environment ready.

| Time | Screen / action | Narration points |
|---|---|---|
| 0:00–0:40 | README tool table | “CampusReads is a demo library assistant. It has exactly three tools: search_catalog is Data, save_reading_item is Action, and plan_reading is Orchestration. Saving updates a local reading list, not a university borrowing system.” |
| 0:40–1:20 | README architecture diagram; agent.py | Explain Host, Client, Server. The Agents SDK host asks the model to choose a discovered tool. The SDK client sends an MCP call to a separate FastMCP process; its result returns to the model and student. |
| 1:20–2:00 | server.py and service.py | Show the three decorators, typed arguments, Pydantic outputs, and annotations. Show plan_reading calling search_catalog then save_reading_item. Explain why shared methods avoid duplicated business logic. |
| 2:00–4:15 | Run the live demo command below | Read each user prompt as it appears. Point at `[DISCOVERY]`, `[CLIENT -> SERVER]`, server logs, `[SERVER -> CLIENT]`, and the assistant's response. Show lookup-only, explicit save, find-and-save, duplicate save, no match, and unknown ID. Pause on the tool calls long enough for viewers to see the selected tool and actual arguments. |
| 4:15–5:00 | Tests and protocol demo | Run pytest. Show that tests check read-only behavior, persistence across service instances, duplicate safety, actual composition order, and errors. Run the no-key protocol demo and point at persisted rows and its final PASS. Explain that this checks the real client/server connection independently of the model. |
| 5:00–5:40 | service.py and reflection | Explain deterministic ranking, the database primary key, no writes on no match, and errors that do not masquerade as success. Discuss the distinction between callable data tools and MCP resources. Mention local sample data and the limits of testing model routing without API access. |
| 5:40–6:00 | Repository and submission checklist | Show your actual repository URL and video location. State one next step: authorized live catalog integration. Close after confirming that all three categories were demonstrated. |

Run in PowerShell:

```powershell
.\.venv\Scripts\python -m library_toolkit.agent --demo
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m library_toolkit.demo
```

Expected live sequence:

1. `search_catalog(query="agents")`: B001 and B005, no save.
2. `save_reading_item(book_id="B001", list_name="demo")`: `created`.
3. `plan_reading(query="machine learning", list_name="demo")`: B004, `created`, both steps.
4. Same orchestration: `already_saved`, original timestamp.
5. Orchestration for underwater basket weaving: `NO_MATCHES`; no save.
6. Save B999: `BOOK_NOT_FOUND`.

The model may phrase queries differently. Explain the actual outputs shown, rather than asserting the expected result if the run differs. If the API is unavailable, fix access before recording; the protocol-only script is supplementary evidence and does not satisfy the agent demonstration by itself. If latency threatens seven minutes, run the interactive host and issue the three successful requests plus one failure, then explain duplicate protection using test output.
