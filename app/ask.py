"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（空行で終了）

ツールを持たない「素の」呼び出し。--chat を付けない場合は会話履歴も持たない。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors
from google.genai.chats import Chat

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat: Chat, question: str) -> str:
    # chat は送受信したメッセージを履歴として保持し、次の質問に一緒に送る
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン] {usage.prompt_token_count}")
        print(f"[出力トークン] {usage.candidates_token_count}\n")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "-c", "--chat", action="store_true", help="会話履歴を保ったまま続けて質問する"
    )
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    question = args.question
    print(f"[質問] {question}\n")
    while True:
        try:
            print(ask(chat, question))
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        if not args.chat:
            break
        try:
            question = input("\n[質問] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:  # 空行で終了
            break
        print()


if __name__ == "__main__":
    main()
