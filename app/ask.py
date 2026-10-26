"""
第1回: 会話履歴を保ちながら質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 質問を省略した場合に最初に使う質問
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat, question: str) -> str:
    """会話履歴を持つchatに質問する。"""
    response = chat.send_message(question)
    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="会話履歴を保ちながら質問する"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")

    try:
        # chatを1回だけ作る。
        # このchatが会話履歴を保持する。
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)

        # 最初の質問は、コマンドラインの質問またはDEFAULT_QUESTION
        question = args.question

        while True:
            print(f"[質問] {question}\n")
            print(ask(chat, question))
            print()

            question = input(
                "続けて質問してください（終了するには exit）："
            )

            if question.lower() == "exit":
                break

    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()