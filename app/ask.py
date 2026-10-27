"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

"""
使い方:
    uv run python -m app.ask --chat

通常は1回だけ質問する。
--chat を付けると、会話履歴を保持して続けて質問できる。
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座固有の質問。正しい内容は data/glossary.json にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


# 単発質問：応答時間とトークン数も確認する
def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())

    start = time.perf_counter()
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
    )
    elapsed = time.perf_counter() - start

    print(f"[応答時間] {elapsed:.2f} 秒")

    # 入力・出力・合計トークン数を表示
    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン] {usage.prompt_token_count}")
        print(f"[出力トークン] {usage.candidates_token_count}")
        print(f"[合計トークン] {usage.total_token_count}")

    return response.text or ""


# 会話履歴を使って連続して質問する
def chat_mode() -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print("対話モード（終了するには exit と入力）")

    while True:
        try:
            question = input("質問：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n対話を終了します。")
            break

        if question.lower() in ("exit", "quit"):
            break

        if not question:
            continue

        response = chat.send_message(question)
        print(response.text or "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini APIに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保持して連続対話する",
    )
    args = parser.parse_args()

    try:
        if args.chat:
            chat_mode()
        else:
            print(f"[model] {MODEL}")
            print(f"[質問] {args.question}\n")
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()