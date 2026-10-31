# Submission checklist

The supplied PDF does not include a numeric marking rubric. This checklist follows every stated requirement; it is not a guarantee of a particular grade.

| PDF requirement | Evidence / file |
|---|---|
| Read Hugging Face article | `docs/summary.md`, including the article's linked full text |
| Explore an existing MCP server | Fetch README and Python source, cited and critiqued in the summary |
| 300–400 word summary | `docs/summary.md` body |
| Exactly one Data tool | `search_catalog` in `library_toolkit/server.py` |
| Exactly one Action tool | `save_reading_item` in the same server |
| Exactly one Orchestration tool | `plan_reading`; composes the data and action implementations |
| Clear descriptions, typed arguments and outputs | Three decorated functions, Field descriptions, and Pydantic output models |
| At least one predictable failure per tool | Invalid query; unknown ID; no matches; tested at the protocol boundary |
| FastMCP server | `library_toolkit/server.py` |
| OpenAI Agents SDK host/client | `library_toolkit/agent.py`: Agent, Runner, MCPServerStdio |
| Unit tests / interactive scripts | `tests/test_toolkit.py` and `library_toolkit/demo.py` |
| Configuration and setup instructions | README, requirements files, `.env.example` |
| Reflection, 1–2 paragraphs | `docs/reflection.md` |
| 5–7 minute screencast | Record using `docs/screencast.md`; still required |
| Repository URL and video URL | Add your actual links below; still required |

Before submission:

- [ ] Review the written summary and personalize the reflection.
- [x] Configure your own API key locally and run `python -m library_toolkit.agent --demo` using the virtual environment.
- [x] Confirm the model visibly invokes all three tools and handles a failure.
- [ ] Record and upload the 5–7 minute screencast.
- [ ] Publish the source repository, excluding secrets, virtual environment, and generated storage.
- [ ] Fill in the real links below; verify your instructor can access them.

Repository URL: https://github.com/Joud158/campusreads-mcp-toolkit

Video URL: **TO BE ADDED BY STUDENT**
