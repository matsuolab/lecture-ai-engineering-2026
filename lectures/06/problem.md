# Lecture 06 Exercises and Homework: Expose and Use Tools Through an MCP Server

## Goals for This Session

- Extract the tools built in Lecture 03 into an **MCP server** and use them **through MCP** from the same agent
- Read the "tool names, descriptions, and arguments" visible to the model
- Add ready-made external tools **just by editing a configuration file**

## Preparation

If you have completed the work from previous sessions, create branch `lec06` from `main`.
This session adds dependencies, so run `uv sync --frozen` once.

```bash
git switch main && git switch -c lec06
uv sync --frozen
```

Otherwise, you can create a branch from the course repository's starting code (the `lec06-start` tag).

```bash
git remote -v                     # If upstream is missing, add it with the next line
git remote add upstream https://github.com/matsuolab/lecture-ai-engineering-2026.git
git fetch upstream --tags
git switch -c lec06 lec06-start
uv sync --frozen
```

## Exercises (30 Minutes)

### 1. List the Tools Visible to the Model

```bash
uv run python -m app.agent --list-tools          # Lecture 03: tools registered directly as functions
uv run python -m app.agent --mcp --list-tools    # Lecture 06: tools received from MCP servers
```

Neither command calls an LLM, so both work without an API key.
The second starts the server (`app/mcp_server.py`) configured in `app/mcp_servers.json` as a subprocess and displays the names, descriptions, and arguments of its exposed tools.

- Check that names have a **"server_name_" prefix**, as in `glossary_search_glossary`. This distinguishes tools with the same name on different servers
- The descriptions come directly from the docstrings in `app/tools.py`. **Function tools and MCP tools look the same to the model**

### 2. Use Them Through MCP from the Agent

```bash
uv run python -m app.agent --mcp --trace "What are the 3 homework levels in the AIE2026 course?"
```

Compare the answer, tool names, and number of `requests` with Lecture 03 (without `--mcp`).
Internally, `build_mcp_agent()` in `app/agent.py` reads the configuration file, starts the servers, and passes their tools to the agent.

### 3. Expose One More Tool

At `TODO(Lecture 06 exercise)` in `app/mcp_server.py`, expose `get_lecture_summary` through MCP too (one line, written the same way as for `search_glossary`).

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "What will we learn in Lecture 02?"
uv run pytest -q
```

Check that `glossary_get_lecture_summary` appears in `--list-tools` and is called in `--trace`.
If you created `make_quiz` in Lecture 03, you can expose it in the same way.

### 4. Add a Ready-Made External Tool Through Configuration Alone

Add the publicly available **fetch server** (retrieves a URL's page and returns it as Markdown) to `app/mcp_servers.json`. No code is needed.

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "Summarize the opening of https://modelcontextprotocol.io/ in 3 lines of English"
```

- The first startup takes about 10 seconds because `uvx` downloads the server
- If `fetch_fetch({'url': ...})` appears in `--trace`, your **Codespace is actually accessing the URL chosen by the model**. Before adding an external tool, understand where it sends data and what it sends
- `INSTRUCTIONS` assumes glossary use. If fetch is not called for a URL question, try adding a line such as "When given a URL, use fetch to read its contents" to `INSTRUCTIONS`

### 5. Submit

Fill in `lectures/06/answer.md` and open a PR from `lec06` to `main` in your own fork.

## Homework (Complete Any One Level)

| Level | Task |
|---|---|
| Basic | Start the server with `uv run python -m app.mcp_server --http`, replace `glossary` in the configuration file with `{"url": "http://127.0.0.1:8000/mcp"}`, and ask the same question. Record how startup, processes, and ports differ between stdio and Streamable HTTP. Also rewrite a tool docstring and compare changes in `--list-tools` and tool calls |
| Implementation | Add Lecture 03's `make_quiz` (or a new tool if you did not create it) to the MCP server and add tests using TestModel in `tests/test_mcp_server.py`. Validate argument ranges (for example, return a clear message for a nonexistent session), and use `--trace` to check how errors through MCP appear to the model |
| Advanced | Use the same glossary server from **Copilot Chat** (VS Code's MCP client; instructions below). Verify that "one server can be used across clients" and compare with use from the agent (`app/agent.py`). Record differences in the steps leading to tool calls (who starts the server, whether a person approves calls beforehand, and how results appear) |

### How to Approach the Advanced Homework

Copilot Chat is an MCP client in VS Code. Place `.vscode/mcp.json` in the repository to use the server's tools in Chat's **Agent** mode (the format uses `servers`, rather than `mcpServers` as in `app/mcp_servers.json`. Commands run in the working folder, which is the repository root).

```json
{
  "servers": {
    "aie-glossary": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    }
  }
}
```

1. Create the file above in VS Code in Codespaces. Click **Start** if it appears above `servers` (otherwise use the command palette: **MCP: List Servers** → `aie-glossary` → Start). The server starts inside your Codespace
2. Open Copilot Chat and switch to **Agent** mode. Check that `search_glossary` from `aie-glossary` appears in the tools (🔧) list (also `get_lecture_summary` if you completed exercise 3)
3. Ask "What are the 3 homework levels in AIE2026?". If asked for confirmation (**Continue**) before tool execution, allow it, and check whether the glossary tool is called and used in the answer
4. In `answer.md`, record the tool call shown in Chat alongside the output from `uv run python -m app.agent --mcp --trace`
5. You may include `.vscode/mcp.json` in the PR (do not put secrets such as API keys in it)

- Copilot Free supports Agent mode and MCP. However, chat has a monthly limit, so keep your trials to a few attempts
- Copilot managed by a company or school (Business / Enterprise) may have MCP disabled by organization policy. Try with a personal account

## Notes

- An MCP server is a **program that executes code**. Do not add servers from unknown sources to your configuration file
- The fetch server accesses URLs chosen by the model. Do not pass internal company URLs or URLs containing personal information
- More tools mean more descriptions sent to the model, increasing tokens per call and making tool selection harder. Use `--list-tools` to keep track of how many tools you provide

## References

- Official MCP site: https://modelcontextprotocol.io/
- Pydantic AI MCP client: https://pydantic.dev/docs/ai/mcp/client/
- MCP Python SDK (how to write servers): https://github.com/modelcontextprotocol/python-sdk
- Public MCP servers: https://github.com/modelcontextprotocol/servers
- Using MCP servers in VS Code: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
