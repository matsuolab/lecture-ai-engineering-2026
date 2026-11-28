"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って続けて質問する

ツールを持たない「素の」呼び出し。
通常は1回だけ質問し、--chat を指定すると会話履歴を保って質問できる。
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


def print_token_usage(response) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 利用情報はありません")
    else:
        print(
            f"[トークン数] 入力トークン数: {usage.prompt_token_count}, "
            f"出力トークン数: {usage.candidates_token_count}"
        )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    print_token_usage(response)
    return response.text


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL)
    print("会話を開始します。「終了」と入力するか Ctrl+D で終了します。")

    while True:
        try:
            question = input("質問> ").strip()
        except EOFError:
            print()
            break

        if question.lower() in {"終了", "exit", "quit"}:
            break
        if not question:
            continue

        response = session.send_message(question)
        print_token_usage(response)
        print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保って続けて質問する",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat:
        try:
            chat()
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
