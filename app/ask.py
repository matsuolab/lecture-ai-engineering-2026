"""第1回: 素のLLMと会話するスクリプト。

使い方:
    uv run python -m app.ask

質問を続けて入力できるが、ツールは持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    conversation = client.chats.create(model=MODEL)

    while True:
        question = input("質問> ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        started_at = time.perf_counter()
        response = conversation.send_message(question)
        elapsed = time.perf_counter() - started_at
        usage = response.usage_metadata
        print(f"[応答時間] {elapsed:.2f}秒")
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")
        print(f"\n{response.text}\n")


def main() -> None:
    argparse.ArgumentParser(description="素のLLMに質問する").parse_args()

    print(f"[model] {MODEL}")
    try:
        chat()
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
