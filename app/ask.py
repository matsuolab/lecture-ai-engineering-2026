"""第1回: Geminiへの単発質問および履歴を保持する対話モード。

使用例:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --chat "自己紹介してください"
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
EXIT_COMMANDS = {"/exit", "/quit"}


def print_token_usage(response: object) -> None:
    """利用情報の欠損と数値0を区別し、SDKが返すtoken数を表示する。"""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        print("[tokens] 利用情報なし")
        return
    input_tokens = getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(usage, "candidates_token_count", None)
    print(f"[tokens] 入力: {input_tokens if input_tokens is not None else '不明'} "
          f"/ 出力: {output_tokens if output_tokens is not None else '不明'}")


def _close(client: object) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


def ask(question: str) -> str:
    """従来の単発API呼び出し（会話履歴を持たない）。"""
    client = genai.Client(api_key=get_api_key())
    try:
        response = client.models.generate_content(model=MODEL, contents=question)
        print_token_usage(response)
        return response.text or "（テキスト応答なし）"
    finally:
        _close(client)


def run_chat(chat_session: object, initial_question: str | None = None) -> None:
    """同一のチャットセッションを再利用し、SDKに会話履歴の管理を任せる。"""
    print("[対話モード] 終了: /exit または /quit")
    pending_question = initial_question
    while True:
        if pending_question is not None:
            question = pending_question.strip()
            pending_question = None
        else:
            try:
                question = input("あなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[対話終了]")
                return
        if question.lower() in EXIT_COMMANDS:
            print("[対話終了]")
            return
        if not question:
            continue
        try:
            response = chat_session.send_message(question)
        except errors.APIError as error:
            print(api_error_message(error.code, error.message))
            continue
        print(f"AI> {response.text or '（テキスト応答なし）'}")
        print_token_usage(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini APIに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保持した対話モード")
    args = parser.parse_args()
    print(f"[model] {MODEL}")
    try:
        if args.chat:
            client = genai.Client(api_key=get_api_key())
            try:
                session = client.chats.create(model=MODEL)
                run_chat(session, initial_question=args.question)
            finally:
                _close(client)
            return
        question = args.question if args.question is not None else DEFAULT_QUESTION
        print(f"[質問] {question}\n")
        print(ask(question))
    except errors.APIError as error:
        print(api_error_message(error.code, error.message))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
