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

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def main() -> None:
    parser = argparse.ArgumentParser(description="LLMと連続して会話する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())

    # 会話履歴を保持するチャットを作成
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("終了するには exit と入力してください。\n")

    question = args.question

    while True:
        try:
            # 質問を送信（過去の会話履歴も保持される）
            response = chat.send_message(question)

            print(f"[質問] {question}")
            print(f"[回答] {response.text}\n")

            # 次の質問を受け取る
            question = input("You: ")

            if question.strip().lower() == "exit":
                break

            if not question.strip():
                continue

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)


if __name__ == "__main__":
    main()