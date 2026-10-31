"""Exercise the actual Runner and stdio host with a scripted model, without API calls.

This tests SDK integration, not natural-language model routing quality.
"""

import asyncio
import json
import os
import sys

from agents import Agent, RunConfig, Runner
from agents.models.interface import Model, ModelResponse
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText

from library_toolkit.agent import ROOT, VisibleMCPServer


class ScriptedModel(Model):
    def __init__(self):
        self.calls = 0

    async def get_response(self, **kwargs):
        self.calls += 1
        assert {t.name for t in kwargs["tools"]} == {"search_catalog", "save_reading_item", "plan_reading"}
        if self.calls == 1:
            requests = [
                ("search_catalog", {"query": "agents"}),
                ("save_reading_item", {"book_id": "B001", "list_name": "direct"}),
                ("plan_reading", {"query": "machine learning", "list_name": "workflow"}),
                ("save_reading_item", {"book_id": "B999", "list_name": "direct"}),
            ]
            output = [ResponseFunctionToolCall(
                type="function_call", name=name, arguments=json.dumps(args), call_id=f"call_{i}"
            ) for i, (name, args) in enumerate(requests)]
        else:
            results = [item for item in kwargs["input"] if isinstance(item, dict) and item.get("type") == "function_call_output"]
            assert len(results) == 4
            combined = json.dumps(results)
            for expected in ["total_matches", "created", "selection_rule", "BOOK_NOT_FOUND"]:
                assert expected in combined
            output = [ResponseOutputMessage(
                id="msg_test", type="message", role="assistant", status="completed",
                content=[ResponseOutputText(type="output_text", text="Verified four real MCP results.", annotations=[])],
            )]
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    async def stream_response(self, **kwargs):
        raise NotImplementedError("This test uses non-streaming Runner.run.")
        yield  # Marks this abstract-interface implementation as an async generator.


def test_runner_round_trip_with_scripted_model_and_real_server(tmp_path, capsys):
    async def scenario():
        model = ScriptedModel()
        async with VisibleMCPServer(
            name="Integration test",
            params={"command": sys.executable, "args": ["-m", "library_toolkit.server"],
                    "cwd": str(ROOT), "env": {**os.environ, "LIBRARY_DB_PATH": str(tmp_path / "agent.sqlite3")}},
            client_session_timeout_seconds=30,
        ) as server:
            agent = Agent(name="Test host", model=model, mcp_servers=[server])
            result = await Runner.run(agent, "Exercise the toolkit.", run_config=RunConfig(tracing_disabled=True))
            assert result.final_output == "Verified four real MCP results."
            assert model.calls == 2
    asyncio.run(scenario())
    printed = capsys.readouterr().out
    assert "[CLIENT -> SERVER]" in printed
    assert "[SERVER -> CLIENT]" in printed
