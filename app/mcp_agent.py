"""第6回: MCP サーバーのツールを使う学習支援エージェント（MCP クライアント）。

使い方:
    uv run python -m app.mcp_agent --list-tools                 # モデルに見えるツール一覧（APIキー不要）
    uv run python -m app.mcp_agent --trace "LoRAとは何ですか？"   # ツール呼び出しを表示

第3回の app/agent.py は、tools.py の関数をエージェントに直接登録した。
このファイルのエージェントは関数を登録しない。設定ファイル（app/mcp_servers.json）に書かれた
MCP サーバーを起動または接続し、サーバーが公開しているツールを受け取って使う。
「モデル + ループ + ツール」の形は第3回と同じで、ツールの受け取り方だけが違う。
"""

import argparse
import inspect
import json
from pathlib import Path

from fastmcp import Client
from mcp.shared.exceptions import MCPError
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UserError
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app.config import MODEL, api_error_message, get_api_key

# 用語集サーバー（app/mcp_server.py）のツールを中心にした指示文。
# 最後の 1 行は、設定ファイルに足したほかのサーバーのツールも使えるようにするためのもの
INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
- 用語集で扱わない質問（Web ページの内容、AWS のドキュメントなど）には、その内容に合うツールがあれば使う。
"""

# 使う MCP サーバーの設定ファイル。Claude Desktop や Cursor と同じ "mcpServers" 形式
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


class ConfigError(Exception):
    """設定ファイル（app/mcp_servers.json）の書き方に誤りがあるときのエラー。"""


def read_config(config_path: Path = MCP_CONFIG) -> dict:
    """設定ファイルを読み、"mcpServers" の中身（サーバー名と設定の対応）を返す。"""
    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    except json.JSONDecodeError as e:
        raise ConfigError(f"{e.lineno} 行目の近くに、JSON の書き方の誤りがあります（{e.msg}）") from e
    except KeyError as e:
        raise ConfigError('"mcpServers" がありません') from e
    for name, spec in config.items():
        if "command" not in spec and "url" not in spec:
            raise ConfigError(f'"{name}" に、"command" も "url" もありません')
    return config


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """設定ファイル（mcpServers 形式）を読み、サーバーごとに接続（MCPToolset）を作る。

    - "command" があれば stdio：サーバーをサブプロセスとして起動する
    - "url" があれば Streamable HTTP：すでに動いているサーバーに接続する
    ツール名には「サーバー名_」を付ける（例: glossary_search_glossary）。複数のサーバーに
    同じ名前のツールがあっても区別できるようにするため。

    Pydantic AI には同じことをする load_mcp_toolsets() もある。ここで自分で組み立てているのは、
    古い SDK で作られたサーバー（fetch など）につなぐとき、接続方式の自動判定（"auto"）が
    警告を大量に出すため。"legacy" に固定すると新旧どちらのサーバーにも静かにつながる。
    """
    toolsets = []
    for name, spec in read_config(config_path).items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def describe_servers(config_path: Path = MCP_CONFIG) -> list[str]:
    """設定ファイルのサーバーごとに、コマンドで起動するのか、URL に接続するのかを 1 行で返す。"""
    lines = []
    for name, spec in read_config(config_path).items():
        if "url" in spec:
            lines.append(f"[server] {name}: URL に接続（{spec['url']}）")
        else:
            command = " ".join([spec["command"], *spec.get("args", [])])
            lines.append(f"[server] {name}: コマンドで起動（{command}）")
    return lines


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    """MCP サーバーが公開するツールだけを使うエージェントを作る。モデルは実行時に渡す。"""
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """モデルに見えているツールの一覧（名前・説明文・引数）を表示する。LLM は呼ばない。

    TestModel（テストで使う偽モデル）にツール一覧を渡し、そこから読み出す。
    """
    model = TestModel(call_tools=[])
    target.run_sync("ツール一覧", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"モデルに見えているツール: {len(tools_seen)} 個")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  引数: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    """どのツールが、どの引数で呼ばれ、何を返したかを表示する。"""
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
            elif isinstance(part, RetryPromptPart) and part.tool_name:
                # ツールが失敗したとき、モデルにはこの内容が渡り、モデルは呼び直すかどうかを決める
                print(f"[tool error]  {part.tool_name} -> {str(part.content)[:120]}")
    usage = result.usage
    print(f"[usage] 入力 {usage.input_tokens:,} tokens / 出力 {usage.output_tokens:,} tokens / モデル応答 {usage.requests} 回")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP サーバーのツールを使う学習支援エージェントに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="ツール呼び出しを表示する")
    parser.add_argument("--list-tools", action="store_true", help="モデルに見えるツール一覧を表示して終了する（APIキー不要）")
    args = parser.parse_args()
    if not args.list_tools and not args.question:
        parser.error("質問を指定してください")

    try:
        target = build_mcp_agent()
        print("\n".join(describe_servers()))
    except ConfigError as e:
        print(f"app/mcp_servers.json を読めませんでした: {e}")
        print("サーバーとサーバーの間に , があるか、最後のサーバーのあとに余分な , がないかを確認してください。")
        raise SystemExit(1)
    try:
        if args.list_tools:
            print_tools(target)
            return
        model = build_model()
        print(f"[model] {MODEL}")
        print(f"[tools] MCP サーバー（{MCP_CONFIG.relative_to(MCP_CONFIG.parent.parent)}）")
        result = target.run_sync(args.question, model=model)
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except (AgentRunError, UserError):
        raise  # エージェントの実行そのもののエラーは、そのまま表示する
    except (MCPError, RuntimeError, OSError) as e:
        # サーバーを起動できない・接続できないとき（コマンド名や URL の誤り、接続先が応答しないなど）
        print(f"MCP サーバーに接続できませんでした: {e}")
        print("app/mcp_servers.json の内容を確認してください。コマンドで起動するサーバーはコマンド名を、URL で接続するサーバーは URL を確認します。")
        raise SystemExit(1)
    print(result.output)
    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
