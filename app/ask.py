"""第1回: 素のLLMに会話履歴を保ったまま続けて質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask              # 質問を省略すると、講座に固有の質問をする

会話履歴を保ちながら、対話形式で続けて質問できるように改修したバージョン。
"""

import argparse
import sys

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def interactive_chat(initial_question: str | None = None) -> None:
    client = genai.Client(api_key=get_api_key())
    # チャットセッションを作成（会話履歴が保持されます）
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("--- 対話モードを開始します (終了するには 'exit' または 'quit' と入力してください) ---\n")

    # 初回質問がある場合は最初に実行
    current_question = initial_question

    while True:
        if not current_question:
            try:
                current_question = input("\n[質問] > ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n終了します。")
                break

            if not current_question:
                continue
            if current_question.lower() in ("exit", "quit"):
                print("終了します。")
                break
        else:
            print(f"[質問] {current_question}")

        try:
            # チャットセッションを通じてメッセージを送信
            response = chat.send_message(current_question)

            # トークン使用量の表示
            if response.usage_metadata:
                print(f"\n[トークン使用量]")
                print(f"  入力トークン数: {response.usage_metadata.prompt_token_count}")
                print(f"  出力トークン数: {response.usage_metadata.candidates_token_count}")
                print("-" * 40)

            print(f"[回答]\n{response.text}")

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            sys.exit(1)

        # 初回質問を処理した後は、ループで入力を受け付けるため None にリセット
        current_question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに会話履歴を保って質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    try:
        interactive_chat(args.question)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()