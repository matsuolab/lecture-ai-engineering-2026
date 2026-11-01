"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive "LoRAとは何ですか？"

ツールを持たない「素の」呼び出し。--interactive では会話履歴を保って質問を続けられる。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai.chats import Chat
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat: Chat, question: str) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else "不明"
    output_tokens = usage.candidates_token_count if usage is not None else "不明"
    print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")

    return response.text


def run_interactive(chat: Chat, initial_question: str | None) -> None:
    question = initial_question.strip() if initial_question else None
    while True:
        if question is None:
            try:
                question = input("質問（終了するには空行）> ").strip()
            except EOFError:
                print()
                return
            if not question:
                return

        print(f"[質問] {question}\n")
        print(ask(chat, question))
        print()
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="会話履歴を保って質問を続ける（空行で終了）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        if args.interactive:
            run_interactive(chat, args.question)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(chat, question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
