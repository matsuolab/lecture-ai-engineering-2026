
"""第1回: Geminiに単発質問・連続質問するスクリプト。

単発質問:
    uv run python -m app.ask "LoRAとは何ですか？"

連続質問:
    uv run python -m app.ask --chat
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(response) -> None:
    """入力・出力トークン数を表示する。"""
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None

    print(f"[入力トークン] {input_tokens if input_tokens is not None else '不明'}")
    print(f"[出力トークン] {output_tokens if output_tokens is not None else '不明'}")


def ask(question: str) -> str:
    """従来の単発質問。"""
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
    )
    print_usage(response)
    return response.text or ""


def chat() -> None:
    """履歴を保持して連続質問する。"""
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("連続質問モードです。終了するときは exit と入力してください。\n")

    while True:
        try:
            question = input("質問> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n終了します。")
            break

        if question.lower() in ("exit", "quit"):
            print("終了します。")
            break

        if not question:
            continue

        try:
            response = session.send_message(question)
            print(f"\n回答> {response.text or '(回答なし)'}\n")
            print_usage(response)
            print()

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Geminiに単発質問・連続質問する"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保持した連続質問モード",
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
