"""第6回: 用語集と各回の要点を MCP サーバーとして公開する。

使い方:
    uv run python -m app.mcp_agent --list-tools     # このサーバーが公開するツールを一覧する（APIキー不要）
    uv run python -m app.mcp_server --http          # Streamable HTTP で起動する（http://127.0.0.1:8000/mcp）
    uv run python -m app.mcp_server --quiz-errors raise        # 宿題（実装）の比較用：範囲外を例外のまま投げる
    uv run python -m app.mcp_server --quiz-errors tool-error   # 宿題（実装）の比較用：範囲外を ToolError で知らせる

引数なしで実行すると stdio（標準入出力）で待ち受ける。これは MCP クライアント（app.mcp_agent など）が
サブプロセスとして起動する使い方なので、手で実行すると入力待ちのまま止まって見える。

第3回では tools.py の関数を agent.py に直接登録した。MCP サーバーにすると、同じ関数を
エージェントのプログラム（app/mcp_agent.py）からも、MCP に対応したほかのソフトウェアからも、
共通の手順で使えるようになる。
"""

import argparse
import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app import tools



def raising_make_quiz(lecture: int, count: int = 1) -> str:
    """比較用：範囲外のときに、メッセージを return せず例外（ValueError）のまま投げる版。"""
    return json.dumps(tools.build_quiz(lecture, count), ensure_ascii=False)


def tool_error_make_quiz(lecture: int, count: int = 1) -> str:
    """比較用：範囲外のときに、MCP の ToolError（ツールの失敗としてメッセージを返す例外）で知らせる版。"""
    try:
        return json.dumps(tools.build_quiz(lecture, count), ensure_ascii=False)
    except tools.QuizArgumentError as e:
        raise ToolError(f"クイズを作れません: {e}") from e


def build_server(quiz_errors: str = "return") -> MCPServer:
    """公開するツールを登録したサーバーを作る。quiz_errors は make_quiz の範囲外の知らせ方。"""
    # サーバーの名前と説明。クライアントに表示される（設定ファイル側のキー "glossary" とは別物）
    target = MCPServer(
        "aie2026-glossary",
        instructions="AIE2026（AIエンジニアリング実践講座）の用語集と各回の要点を提供する。",
    )

    # 第3回と同じ関数を、そのまま MCP のツールとして公開する。docstring と型ヒントが説明文になる
    target.tool()(tools.search_glossary)

    # TODO(宿題・基礎): get_lecture_summary も公開しよう
    target.tool()(tools.get_lecture_summary)

    # 宿題（実装）：確認問題を作るツール。処理は tools.py に置き、ここでは公開だけを行う
    # 比較用の版も、名前と説明文は同じにして、違いを「範囲外の知らせ方」だけにする
    variants = {"return": tools.make_quiz, "raise": raising_make_quiz, "tool-error": tool_error_make_quiz}
    target.tool(name="make_quiz", description=tools.make_quiz.__doc__)(variants[quiz_errors])
    return target


server = build_server()


def main() -> None:
    parser = argparse.ArgumentParser(description="用語集 MCP サーバー")
    parser.add_argument("--http", action="store_true", help="Streamable HTTP で起動する（既定は stdio）")
    parser.add_argument("--quiz-errors", choices=["return", "raise", "tool-error"], default="return",
                        help="make_quiz の範囲外の知らせ方（宿題・実装の比較用。既定は return）")
    args = parser.parse_args()
    target = build_server(args.quiz_errors)
    if args.http:
        print("MCP サーバーを http://127.0.0.1:8000/mcp で起動します（Ctrl+C で停止）")
        target.run(transport="streamable-http")
    else:
        # stdio では標準出力がプロトコルの通信路になるので、print してはいけない
        target.run()


if __name__ == "__main__":
    main()
