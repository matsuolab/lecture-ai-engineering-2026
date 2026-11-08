"""第3回: Pydantic AI で作る学習支援エージェント。

使い方:
    uv run python -m app.agent "AIE2026の講座で使う「lecNN-start タグ」とは何ですか？"
    uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"   # ツール呼び出しを表示
    uv run python -m app.agent --mcp --trace "LoRAとは？"        # 第5回: ツールを MCP サーバーから受け取る
    uv run python -m app.agent --mcp --list-tools               # 第5回: モデルに見えるツール一覧（APIキー不要）

エージェント = モデル + ループ + ツール。
モデルは tools.py の関数を「ツール」として呼び出し、その結果を見て回答を作る。
第5回では、同じツールを MCP サーバー（app/mcp_server.py）経由で受け取る。
"""

import argparse
import inspect
import json
from pathlib import Path

import re
import unicodedata

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.exceptions import ModelHTTPError
from fastmcp import Client
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
- モードの判別:
    - 学習記録の保存を希望されたら、講義回・用語・理解度・次のアクションを確認する。理解度はhigh / medium / lowから選び、middleとは言わない。
    - 情報が不足している間は、不足項目だけを質問する。保存モード中の「2回」などの返答は、直前の質問への回答として扱い、講義の説明に切り替えない。
    - 4項目がそろったら save_learning_log を呼び出す。保存後は完了を伝える。
    - 保存以外の質問では、質問に応じて検索・要約・クイズのツールを使う。
"""

# モデルは実行時に渡す（テストではAPIを呼ばない TestModel に差し替えるため）
agent = Agent(instructions=INSTRUCTIONS, output_type=[str, DeferredToolRequests])
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)

# TODO(第3回 演習): tools.py に make_quiz を作り、ここで登録しよう
agent.tool_plain(tools.make_quiz) 
# 第３回宿題学習ログ機能の追加
agent.tool_plain(tools.save_learning_log, requires_approval=True)
agent.tool_plain(tools.get_pending_topics)



# 第5回: 使う MCP サーバーの設定ファイル。Claude Desktop や Cursor と同じ "mcpServers" 形式
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """設定ファイル（mcpServers 形式）を読み、サーバーごとに接続（MCPToolset）を作る。

    - "command" があれば stdio：サーバーをサブプロセスとして起動する
    - "url" があれば Streamable HTTP：起動済みのサーバーに接続する
    ツール名には「サーバー名_」を付ける（例: glossary_search_glossary）。複数のサーバーに
    同じ名前のツールがあっても区別できるようにするため。

    Pydantic AI には同じことをする load_mcp_toolsets() もある。ここで自分で組み立てているのは、
    古い SDK で作られたサーバー（fetch など）につなぐとき、接続方式の自動判定（"auto"）が
    警告を大量に出すため。"legacy" に固定すると新旧どちらのサーバーにも静かにつながる。
    """
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    toolsets = []
    for name, spec in config.items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    """第5回: 関数を直接登録する代わりに、MCP サーバーが公開するツールを使うエージェント。INSTRUCTIONS は同じ。"""
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """モデルに見えているツールの一覧（名前・説明文・引数）を表示する。LLM は呼ばない。

    TestModel（テストで使う偽モデル）にツール一覧を渡し、そこから読み出す。
    MCP サーバーのツールも、第3回の関数ツールも、モデルから見れば同じ形をしている。
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
    print(f"[usage] {result.usage}")


# 第3回宿題学習ログ機能の追加

def is_learning_log_request(text: str) -> bool:
    text = unicodedata.normalize("NFKC", text)
    return (
        ("学習の記録" in text or "学習記録" in text or "学習ログ" in text)
        and any(word in text for word in ("したい", "保存", "記録して", "残したい"))
    )


def collect_learning_log() -> dict | None:
    while True:
        raw = unicodedata.normalize(
            "NFKC", input("講義回は何回ですか？（例: 2回）: ").strip()
        )
        match = re.fullmatch(r"(?:第\s*)?(\d+)\s*回?", raw)
        if match and int(match.group(1)) > 0:
            lecture = int(match.group(1))
            break
        print("講義回を「2回」のように入力してください。")

    def ask_nonempty(prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("空欄にはできません。入力してください。")

    term = ask_nonempty("用語は何ですか？: ")

    while True:
        understanding = input("理解度を high / medium / low で入力してください: ")
        understanding = understanding.strip().lower()
        if understanding in {"high", "medium", "low"}:
            break
        print("high / medium / low のいずれかで入力してください。")

    next_action = ask_nonempty("次のアクションは何ですか？: ")

    print(f"\n第{lecture}回 / {term} / {understanding} / {next_action}")
    # while True:
    #     answer = input("この内容で保存要求を出しますか？ [y/n]: ").strip().lower()
    #     if answer in {"y", "yes"}:
    #         return {
    #             "lecture": lecture,
    #             "term": term,
    #             "understanding": understanding,
    #             "next_action": next_action,
    #         }
    return {
        "lecture": lecture,
        "term": term,
        "understanding": understanding,
        "next_action": next_action,
    }   
        # if answer in {"n", "no"}:
        #     print("保存をキャンセルしました。")
        #     return None
        # print("y または n で答えてください。")

def ask_tool_approval(tool_name: str) -> bool:
    while True:
        answer = input(
            f"{tool_name} を実行してよいですか？ [y/N] "
        ).strip().lower()

        if answer in {"y", "yes"}:
            return True
        if answer in {"", "n", "no"}:
            return False
        print("y または n で答えてください。")

def request_log_save(data: dict, trace: bool = False) -> None:
    prompt = (
        "次の確認済みデータを使い、save_learning_logを一度だけ呼び出してください。"
        "値を推測・変更せず、他のツールは呼び出さないでください。\n"
        f"{json.dumps(data, ensure_ascii=False)}"
    )

    # 通常の会話履歴とは分けて、保存処理だけを実行する
    result = agent.run_sync(prompt, model=build_model(), message_history=[])

    while isinstance(result.output, DeferredToolRequests):
        requests = result.output
        approvals = {}

        for call in requests.approvals:
            approvals[call.tool_call_id] = ask_tool_approval(call.tool_name)

        if not all(approvals.values()):
            if trace:
                print_trace(result)
            print("保存をキャンセルしました。")
            return

        result = agent.run_sync(
            None,
            model=build_model(),
            message_history=result.all_messages(),
            deferred_tool_results=DeferredToolResults(approvals=approvals),
        )
        
    print(result.output)
    if trace:
        print_trace(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="学習支援エージェントに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="ツール呼び出しを表示する")
    parser.add_argument("--mcp", action="store_true", help="第5回: ツールを MCP サーバー（app/mcp_servers.json）から受け取る")
    parser.add_argument("--list-tools", action="store_true", help="モデルに見えるツール一覧を表示して終了する（APIキー不要）")
    args = parser.parse_args()

    target = build_mcp_agent() if args.mcp else agent
    if args.list_tools:
        print_tools(target)
        return
    if not args.question:
        parser.error("質問を指定してください")

    print(f"[model] {MODEL}")
    if args.mcp:
        print("[tools] MCP サーバー（app/mcp_servers.json）")
    
    # --- クイズのやり取りのため、ここからをループに変更する ---
    history = []
    user_input = args.question

    while True:
        if user_input is None:
            user_input = input("\nユーザー: ").strip()

        if user_input.lower() in {"exit", "quit", "終了"}:
            break

        if is_learning_log_request(user_input):
            data = collect_learning_log()
            if data is not None:
                request_log_save(data, trace=args.trace)
            user_input = None
            continue

        try:
            result = target.run_sync(
                user_input,
                model=build_model(),
                message_history=history,
            )

            while isinstance(result.output, DeferredToolRequests):
                requests = result.output
                history = result.all_messages()

                approvals = {}
                for call in requests.approvals:
                    approvals[call.tool_call_id] = ask_tool_approval(call.tool_name)

                result = target.run_sync(
                    None,
                    model=build_model(),
                    message_history=history,
                    deferred_tool_results=DeferredToolResults(approvals=approvals),
                )

            history = result.all_messages()
            print(f"AI: {result.output}")

            if args.trace:
                print_trace(result)

        except ModelHTTPError as e:
            print(api_error_message(e.status_code, str(e.body)[:200]))
            break

        user_input = None 
    
    # try:
    #     result = target.run_sync(args.question, model=build_model())
    # except ModelHTTPError as e:
    #     print(api_error_message(e.status_code, str(e.body)[:200]))
    #     raise SystemExit(1)
    # print(result.output)
    # if args.trace:
    #     print_trace(result)




if __name__ == "__main__":
    main()
