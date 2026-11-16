"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（宿題：実装）

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(response) -> None:
    """response.usage_metadata から入力・出力トークン数を表示する。"""
    usage = response.usage_metadata
    if usage is None:
        print("[tokens] 取得できませんでした")
        return
    # 返らないことがあるので、None は 0 として扱う
    prompt = usage.prompt_token_count or 0
    output = usage.candidates_token_count or 0
    print(f"[tokens] 入力: {prompt} / 出力: {output}")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    print_usage(response)

    return response.text


def chat() -> None:
    """会話履歴を保ったまま続けて質問する。空行・exit・quit で終了。"""
    client = genai.Client(api_key=get_api_key())
    # chats.create はこれまでのやりとりを内部に保持し、毎回まとめて送る
    session = client.chats.create(model=MODEL)
    print("会話モード（空行・exit・quit で終了）")
    while True:
        try:
            question = input("\n[質問] ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question in ("", "exit", "quit"):
            break
        response = session.send_message(question)
        print_usage(response)
        print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保ったまま続けて質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            chat()
            return
        print(f"[質問] {args.question}\n")
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
