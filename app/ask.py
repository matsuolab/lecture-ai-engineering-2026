"""第1回演習: Geminiへの単発質問と、履歴を引き継ぐ連続質問。

単発質問:
    uv run python -m app.ask "LoRAとは何ですか？"
連続質問:
    uv run python -m app.ask --chat
終了するには /exit と入力。
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def show_token_counts(response) -> None:
    """Gemini APIの応答メタデータからトークン数を表示する。"""
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 取得できませんでした")
        return

    input_tokens = usage.prompt_token_count
    output_tokens = usage.candidates_token_count
    print(f"[入力トークン数] {input_tokens if input_tokens is not None else '不明'}")
    print(f"[出力トークン数] {output_tokens if output_tokens is not None else '不明'}")


def ask(question: str) -> str:
    """従来の単発質問機能。"""
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    show_token_counts(response)
    return response.text or ""


def chat_loop(first_question: str | None = None) -> None:
    """同一チャットを使って、前の質問・回答を踏まえた会話を続ける。"""
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print("会話モードです。終了する場合は /exit と入力してください。")
    question = first_question

    while True:
        if question is None:
            try:
                question = input("あなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n会話を終了しました。")
                break

        if question.lower() in ("/exit", "exit", "/quit", "quit"):
            print("会話を終了しました。")
            break
        if not question:
            question = None
            continue

        try:
            response = chat.send_message(question)
        except errors.APIError as exc:
            print(api_error_message(exc.code, exc.message))
            raise SystemExit(1) from exc

        print(f"AI> {response.text or '（回答テキストなし）'}")
        show_token_counts(response)
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Geminiへの単発質問・連続質問")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保って連続質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat:
        chat_loop(args.question)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as exc:
        print(api_error_message(exc.code, exc.message))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
