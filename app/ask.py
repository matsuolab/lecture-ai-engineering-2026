"""第1回: Gemini と会話するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問後も続けて質問できる

同じチャットに質問を送り続けるため、会話履歴を保ったまま質問できる。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat, question: str) -> str:
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed = time.perf_counter() - started_at

    usage = response.usage_metadata
    print(f"[time] 応答時間: {elapsed:.2f}秒")
    print(f"[usage] 入力トークン: {usage.prompt_token_count}, 出力トークン: {usage.candidates_token_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        question = args.question
        while question:
            print(f"[質問] {question}\n")
            print(ask(chat, question))
            try:
                question = input("\n質問（終了するには Ctrl-D）: ").strip()
            except EOFError:
                print()
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
