"""第6回: MCP サーバーとクライアントの配線テスト（LLM も API キーも使わない）。

app/mcp_servers.json の glossary サーバーを実際に起動し（stdio）、TestModel で
「ツールが MCP 経由で公開され、呼ばれ、結果が戻るか」を確かめる。
"""

import json

import pytest
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.mcp_agent import (
    MCP_CONFIG,
    ConfigError,
    build_mcp_agent,
    describe_servers,
    read_config,
)

GLOSSARY_TOOL = "glossary_search_glossary"  # 設定ファイルのサーバー名 "glossary" が前に付く
QUIZ_TOOL = "glossary_make_quiz"


def _glossary_only_config(tmp_path):
    """設定のうち glossary サーバーだけを使う（演習で足した fetch などの外部サーバーは起動しない）。"""
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    assert "glossary" in config["mcpServers"], "app/mcp_servers.json に glossary サーバーが必要"
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps({"mcpServers": {"glossary": config["mcpServers"]["glossary"]}}), encoding="utf-8"
    )
    return path


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_glossary_server_exposes_search_tool(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("ツール一覧", model=model)

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert GLOSSARY_TOOL in offered  # 宿題でツールを足しても壊れないよう「含む」で判定


def test_make_quiz_is_exposed_through_mcp(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("確認問題", model=model)

    offered = {tool.name for tool in model.last_model_request_parameters.function_tools}
    assert QUIZ_TOOL in offered


def test_make_quiz_result_comes_back_through_mcp(tmp_path):
    model = TestModel(call_tools=[QUIZ_TOOL])
    result = build_mcp_agent(_glossary_only_config(tmp_path)).run_sync(
        "第99回のクイズを作って", model=model
    )

    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == QUIZ_TOOL
    assert "第0回" in str(returns[0].content)


def test_glossary_result_comes_back_through_mcp(tmp_path):
    model = TestModel(call_tools=[GLOSSARY_TOOL])
    result = build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("LoRAとは？", model=model)

    assert [p.tool_name for p in _parts(result, ToolCallPart)] == [GLOSSARY_TOOL]
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == GLOSSARY_TOOL
    assert str(returns[0].content).strip()  # 検索結果（または「見つかりませんでした」）が戻っている
    assert result.output


def test_describe_servers_tells_command_from_url(tmp_path):
    """コマンドで起動するサーバーと、URL で接続するサーバーを、表示で見分けられる。"""
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "glossary": {"command": "uv", "args": ["run", "python", "-m", "app.mcp_server"]},
                    "aws": {"url": "https://knowledge-mcp.global.api.aws"},
                }
            }
        ),
        encoding="utf-8",
    )
    assert describe_servers(path) == [
        "[server] glossary: コマンドで起動（uv run python -m app.mcp_server）",
        "[server] aws: URL に接続（https://knowledge-mcp.global.api.aws）",
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"mcpServers": {"a": {"command": "uv"} "b": {"url": "https://example.com"}}}', "JSON の書き方の誤り"),
        ('{"servers": {}}', '"mcpServers" がありません'),
        ('{"mcpServers": {"a": {"args": []}}}', '"command" も "url" もありません'),
    ],
)
def test_config_mistakes_are_reported_in_words(tmp_path, text, expected):
    """設定ファイルの書き間違いは、どこをどう直すかが分かる言葉で知らせる。"""
    path = tmp_path / "mcp_servers.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match=expected):
        read_config(path)
