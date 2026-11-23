"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    usage = response.usage_metadata
    if usage is None:
        print("[usage] トークン使用量を取得できませんでした")
    else:
        print(
            f"[usage] 入力トークン数: {usage.prompt_token_count}, "
            f"出力トークン数: {usage.candidates_token_count}"
        )

    return response.text


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)  # client の直後に一度だけ作る

    while True:
        question = input("質問（終了は exit）> ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        response = chat.send_message(question)
        print(response.text)


if __name__ == "__main__":
    main()
