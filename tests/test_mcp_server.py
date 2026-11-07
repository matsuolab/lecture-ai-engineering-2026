"""Lecture 06: MCP server/client wiring tests (no LLM or API key used).

Actually start the glossary server from app/mcp_servers.json (stdio), and use TestModel
to check that tools are exposed through MCP, called, and return results.
"""

import json

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import MCP_CONFIG, build_mcp_agent

GLOSSARY_TOOL = "glossary_search_glossary"  # Prefixed with the configuration file server name "glossary"


def _glossary_only_config(tmp_path):
    """Use only the glossary server from the configuration (do not start external servers such as fetch added in exercises)."""
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    assert "glossary" in config["mcpServers"], "app/mcp_servers.json must include a glossary server"
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps({"mcpServers": {"glossary": config["mcpServers"]["glossary"]}}), encoding="utf-8"
    )
    return path


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_glossary_server_exposes_search_tool(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("Tool list", model=model)

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert GLOSSARY_TOOL in offered  # Check inclusion so adding tools in the exercises does not break the test


def test_glossary_result_comes_back_through_mcp(tmp_path):
    model = TestModel(call_tools=[GLOSSARY_TOOL])
    result = build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("What is LoRA?", model=model)

    assert [p.tool_name for p in _parts(result, ToolCallPart)] == [GLOSSARY_TOOL]
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == GLOSSARY_TOOL
    assert str(returns[0].content).strip()  # A search result (or a "not found" message) was returned
    assert result.output
