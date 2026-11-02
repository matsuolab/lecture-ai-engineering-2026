"""第1回: 会話履歴を保ちながらLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールを持たない「素の」呼び出し。
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


def ask(chat, question: str) -> tuple[str, int, int]:
    """同じChatに質問を送り、Chatが管理する会話履歴を使う。"""
    response = chat.send_message(question)

    return (
        response.text,
        response.usage_metadata.prompt_token_count,
        response.usage_metadata.candidates_token_count,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)

    question = args.question
    while True:
        print(f"[質問] {question}\n")
        try:
            answer, input_tokens, output_tokens = ask(chat, question)
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        print(answer)
        print(f"[入力トークン数] {input_tokens}")
        print(f"[出力トークン数] {output_tokens}")

        try:
            question = input("\n続けて質問してください（終了: exit）: ")
        except EOFError:
            print()
            break
        if question.strip().lower() in {"exit", "quit"}:
            break


if __name__ == "__main__":
    main()
