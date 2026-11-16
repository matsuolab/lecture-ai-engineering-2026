"
"""第1回: 会話履歴を保持して連続で質問するスクリプト。

使い方:
    uv run python -m app.ask

質問と回答を履歴に保存し、次の質問でも過去の会話を参照できる。
終了するには exit と入力する。
"""


import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"



def ask(question: str, history: list) -> str:
    client = genai.Client(api_key=get_api_key())

    response = client.models.generate_content(
        model=MODEL,
        contents=history + [
            {"role": "user", "parts": [{"text": question}]}
        ]
    )

    answer = response.text

    if answer is not None:
        history.append(
            {"role": "user", "parts": [{"text": question}]}
        )
        history.append(
            {"role": "model", "parts": [{"text": answer}]}
        )

    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    args = parser.parse_args()

    history = []

    print(f"[model] {MODEL}")
    print("終了するには exit と入力してください。")

    question = args.question

    while True:
        if question is None:
            question = input("\n質問: ")

        if question.lower() == "exit":
            break

        if not question.strip():
            question = None
            continue

        try:
            print(ask(question, history))
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        question = None

if __name__ == "__main__":
    main()
