"""第1回: 素のLLMに質問するスクリプト（会話履歴を保持）。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

最初の質問のあとは入力待ちになり、続けて質問できる。
会話履歴（これまでの質問と回答）を保ったまま次の質問に答えるので、
「さっきの話の続き」のような聞き方もできる。空行または Ctrl-D で終了する。

ツールは持たない「素の」呼び出し。講座に固有のことを聞くと、「分からない」と
答えるか、一般論でもっともらしく答える（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat, question: str) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    print(
        f"[トークン数] 入力: {usage.prompt_token_count} "
        f"/ 出力: {usage.candidates_token_count}"
    )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLMに質問する（会話履歴を保持し、続けて質問できる）"
    )
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print("会話履歴を保ったまま続けて質問できます。空行または Ctrl-D で終了します。\n")

    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    question = args.question
    while question:
        print(f"[質問] {question}\n")
        try:
            print(ask(chat, question))
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        print()
        try:
            question = input("[次の質問] ").strip()
        except EOFError:
            break


if __name__ == "__main__":
    main()
