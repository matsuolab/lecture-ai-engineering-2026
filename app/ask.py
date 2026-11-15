"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って続けて質問する

ツールを使わない「素の」呼び出し。--chat を指定すると会話履歴を保って続けて質問できる。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from dataclasses import dataclass

from google import genai
from google.genai import errors
from google.genai.chats import Chat

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


@dataclass
class _ChatSession:
    client: genai.Client
    chat: Chat


def create_chat() -> _ChatSession:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    return _ChatSession(client=client, chat=chat)


def ask(question: str, chat: Chat | None = None) -> str:
    if chat is None:
        session = create_chat()
        chat = session.chat
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is None:
        input_tokens = output_tokens = "不明"
    else:
        input_tokens = (
            usage.prompt_token_count
            if usage.prompt_token_count is not None
            else "不明"
        )
        output_tokens = (
            usage.candidates_token_count
            if usage.candidates_token_count is not None
            else "不明"
        )
    print(f"[トークン数] 入力: {input_tokens} / 出力: {output_tokens}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="同じ会話履歴を保って続けて質問する",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if not args.chat:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
            return

        session = create_chat()
        chat = session.chat
        question = args.question
        while True:
            if question is None:
                try:
                    question = input("質問> ")
                except EOFError:
                    print()
                    break
            if question.strip().lower() in {"exit", "quit", "終了"}:
                break
            if not question.strip():
                question = None
                continue

            print(f"[質問] {question}\n")
            print(ask(question, chat))
            question = None
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
