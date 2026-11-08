"""第1回: 素のLLMに対話形式で質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask

ツールは使わず、会話履歴を保持して質問する「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題の3レベル（基礎・実装・発展）とは何ですか？"

def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに対話形式で質問する")
    parser.add_argument("question", nargs="?", help="最初に送る質問")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(
        model=MODEL,
        config={"temperature": 0.0},
    )

    question = args.question
    try:
        while True:
            if question is None:
                try:
                    question = input("質問> ").strip()
                except EOFError:
                    print()
                    break

            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                question = None
                continue

            start_time = time.perf_counter()
            response = chat.send_message(question)
            elapsed_time = time.perf_counter() - start_time
            print(f"応答時間: {elapsed_time:.2f} 秒")
            usage = response.usage_metadata
            if usage is not None:
                print(
                    f"[tokens] input={usage.prompt_token_count} "
                    f"output={usage.candidates_token_count}"
                )
            print(response.text)
            question = None
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
