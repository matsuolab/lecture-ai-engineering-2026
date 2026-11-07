"""Lecture 06: expose the glossary and session key points through an MCP server.

Usage:
    uv run python -m app.agent --mcp --list-tools   # List tools exposed by this server (no API key needed)
    uv run python -m app.mcp_server --http          # Start with Streamable HTTP (http://127.0.0.1:8000/mcp)

With no arguments, listen on stdio (standard input/output). This mode is meant for an MCP client
(app.agent with --mcp or Copilot Chat) to start the server as a subprocess. If you run it manually,
it appears to hang while waiting for input.

In Lecture 03, we registered functions from tools.py directly in agent.py. An MCP server lets clients
other than Pydantic AI (such as Copilot Chat) use the same functions through a shared protocol.
"""

import argparse

from mcp.server.mcpserver import MCPServer

from app import tools

# Server name and description, shown to clients (distinct from the "glossary" key in the configuration file)
server = MCPServer(
    "aie2026-glossary",
    instructions="Provides the glossary and session key points for AIE2026 (AI Engineering Pilot Course).",
)

# Expose the same function as in Lecture 03 as an MCP tool. Its docstring and type hints become the description
server.tool()(tools.search_glossary)

# TODO(Lecture 06 exercise): expose tools.get_lecture_summary too (the same form as the line above)
# If you created make_quiz in Lecture 03, you can expose it too


def main() -> None:
    parser = argparse.ArgumentParser(description="Glossary MCP server")
    parser.add_argument("--http", action="store_true", help="Start with Streamable HTTP (default: stdio)")
    args = parser.parse_args()
    if args.http:
        print("Starting the MCP server at http://127.0.0.1:8000/mcp (Ctrl+C to stop)")
        server.run(transport="streamable-http")
    else:
        # With stdio, standard output carries protocol messages, so do not print to it
        server.run()


if __name__ == "__main__":
    main()
