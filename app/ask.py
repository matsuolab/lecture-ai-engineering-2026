
"""第1回: Gemini APIに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask
    uv run python -m app.ask --chat
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key


DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def show_tokens(response) -> None:
    """入力・出力トークン数を表示する。"""
    usage = response.usage_metadata

    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")
        print()


def ask(question: str) -> str:
    """1回だけ質問する。"""
    client = genai.Client(api_key=get_api_key())

    response = client.models.generate_content(
        model=MODEL,
        contents=question,
    )

    show_tokens(response)
    return response.text or ""


def chat() -> None:
    """会話履歴を保持して連続質問する。"""
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("チャットを開始します。")
    print("終了するには exit と入力してください。\n")

    while True:
        try:
            question = input("あなた > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nチャットを終了します。")
            break

        if question.lower() in ("exit", "quit"):
            print("チャットを終了します。")
            break

        if not question:
            continue

        try:
            response = session.send_message(question)
            print(f"\nGemini > {response.text or ''}\n")
            show_tokens(response)

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))


def main() -> None:
    """コマンドライン引数に応じて動作を切り替える。"""
    parser = argparse.ArgumentParser(description="Gemini APIに質問する")

    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
    )

    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保持して連続質問する",
    )

    args = parser.parse_args()

    if args.chat:
        chat()
        return

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")

    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
