"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --interactive "LoRAとは何ですか？"
    uv run python -m app.ask --interactive  # 質問を続ける。空行で終了

ツールを持たない「素の」呼び出し。--interactive では会話履歴を保って続けて質問できる。
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


def create_chat() -> tuple[genai.Client, Chat]:
    client = genai.Client(api_key=get_api_key())
    return client, client.chats.create(model=MODEL)


def ask(question: str, chat: Chat | None = None) -> str:
    if chat is None:
        client, chat = create_chat()
    response = chat.send_message(question)

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage and usage.prompt_token_count is not None else "不明"
    output_tokens = usage.candidates_token_count if usage and usage.candidates_token_count is not None else "不明"
    print(f"[tokens] 入力: {input_tokens}, 出力: {output_tokens}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--interactive", action="store_true", help="会話履歴を保って続けて質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.interactive:
            print("[会話] 空行で終了します")
            client, chat = create_chat()
            question = args.question
            while True:
                if question is None:
                    try:
                        question = input("質問> ")
                    except EOFError:
                        print()
                        break
                if not question.strip():
                    break
                print(f"[質問] {question}\n")
                print(ask(question, chat))
                question = None
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
