"""第1回: 会話履歴を保ちながらLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問から会話を始める
    # 続けて質問し、/exit で終了

ツールを持たない「素の」チャット。会話履歴はチャットセッション中保持される。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_response(response: genai.types.GenerateContentResponse) -> None:
    print(response.text)
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 使用量情報を取得できませんでした")
    else:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )


def run_conversation(first_question: str) -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    question = first_question
    while True:
        print(f"[質問] {question}")
        print_response(chat.send_message(question))

        try:
            question = input("\n質問を入力してください（/exit で終了）: ")
        except EOFError:
            print()
            break
        if question.strip().lower() in {"/exit", "/quit"}:
            break
        if not question.strip():
            continue


def main() -> None:
    parser = argparse.ArgumentParser(
        description="会話履歴を保ちながら素のLLMに質問する"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="会話の最初の質問（省略時は講座に固有の既定の質問）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        run_conversation(args.question)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
