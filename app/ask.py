"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保持して連続で質問する

ツールを持たない「素の」呼び出し。
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


def print_usage(response) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[usage] unavailable")
    else:
        print(
            f"[usage] input_tokens={usage.prompt_token_count} "
            f"output_tokens={usage.candidates_token_count}"
        )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    print_usage(response)
    return response.text


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    conversation = client.chats.create(model=MODEL)
    print("対話を開始します。終了するには exit または 終了 と入力してください。")

    while True:
        try:
            question = input("質問> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if question.strip() in ("exit", "終了"):
            break

        try:
            response = conversation.send_message(question)
        except KeyboardInterrupt:
            print()
            break

        print(response.text)
        print_usage(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保持して連続で質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat:
        try:
            chat()
        except KeyboardInterrupt:
            print()
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)
        return

    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
