
# Answer to Question 6

## Exercise

<!-- Please paste the line that says [tool call] exactly as it appears. You can leave any unfinished STEPs blank. -->

- Name of the tool in STEP 1: `glossary_search_glossary`
- STEP 2 [tool call]: `glossary_search_glossary({'query': '3 levels'})`
- STEP 3 [tool call]: `fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
- STEP 4 [tool call]:
- Observations and questions: MCP separates the agent/client (`app/mcp_agent.py`) from tool execution (`app/mcp_server.py` or external servers), while passing tool names, descriptions, and argument schemas to the model. Local tools run via `command` (`stdio`), whereas remote servers connect via `url` over HTTP, so checking server trust and permissions before adding external servers is important.

## homework

<!-- Completing one of the following–basic, implementation, or advanced–will finish the project. -->

-Levels worked: All Levels

-Things I did:
  - **Basic:** Published `get_lecture_summary` on the `glossary` MCP server by adding `server.tool()(tools.get_lecture_summary)` in `app/mcp_server.py` without modifying `app/mcp_agent.py` or `app/mcp_servers.json`.

  - **Implementation:** Added `make_quiz` to `app/tools.py` with lecture-number validation returning a clear message when out of range, and published `server.tool()(tools.make_quiz)` in `app/mcp_server.py`.

  - **Advanced:** Researched MCP server configuration in Visual Studio Code's official documentation (`https://code.visualstudio.com/docs/agents/reference/mcp-configuration` and `https://code.visualstudio.com/docs/agent-customization/mcp-servers`, checked November 27, 2026) and compared it against `app/mcp_servers.json`.

-result :
  - **Basic:** `git status` showed only `app/mcp_server.py` modified; `--list-tools` listed `glossary_get_lecture_summary`; `--trace "What do we learn in Lecture 2?"` called `glossary_get_lecture_summary({'lecture': 2})` (2 model responses, 1,274 in / 185 out tokens); `uv run pytest -q` passed all 21 tests.

  - **Implementation:** `--list-tools` showed 3 tools (`glossary_search_glossary`, `glossary_get_lecture_summary`, `glossary_make_quiz`). Running `--trace "Create a quiz for Lecture 99."` invoked `glossary_make_quiz({'lecture': 99})`, returned the out-of-range message (`valid range: 1–6...`) in `[tool return]` (2 model responses, 978 in / 128 out tokens), and let the model report that Lecture 99 does not exist and list available lectures instead of guessing. `uv run pytest -q` passed all 21 tests.
  - **Advanced (VS Code vs. `app/mcp_servers.json`, checked 2026-11-27):**

    - **Where configured:** `app/mcp_servers.json` uses a single repo file with `"mcpServers"`. VS Code supports command/UI setup (`MCP: Add Server`, `code --add-mcp`), `.mcp.json` (root `"mcpServers"`), `~/.copilot/mcp-config.json` (root `"mcpServers"`), and `.vscode/mcp.json` or user `mcp.json` (root `"servers"`).

    - **Command counterpart:** Both use `"command"` and `"args"` (stdio); VS Code additionally supports `"env"`, `"envFile"`, `"inputs"`, `"sandbox"`, and explicit `"type": "stdio"` in `.vscode/mcp.json`.

    - **URL counterpart:** `app/mcp_servers.json` uses `"url"` directly, whereas VS Code pairs `"url"` with `"type": "http"` or `"type": "sse"` (plus optional `"headers"` and OAuth).
    
    - **Scope:** `app/mcp_servers.json` is project-local to this repository's agent, whereas VS Code supports both project/workspace scope (`.mcp.json`, `.vscode/mcp.json`) and cross-project user/global scope (`~/.copilot/mcp-config.json`, user profile `mcp.json`).
- Observations and questions: Because the agent queries published tools dynamically on startup, adding tools in `app/mcp_server.py` works immediately without changing `app/mcp_agent.py`. Returning explicit, actionable validation messages on out-of-range tool arguments helps the model self-correct or abstain cleanly rather than hallucinating missing data.