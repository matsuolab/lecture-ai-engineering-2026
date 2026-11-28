"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive  # 会話履歴を保って続けて質問する

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


def _print_usage(response) -> None:
    usage = response.usage_metadata
    input_tokens = getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(usage, "candidates_token_count", None)
    print(
        f"[tokens] 入力: {input_tokens if input_tokens is not None else '不明'}, "
        f"出力: {output_tokens if output_tokens is not None else '不明'}"
    )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    _print_usage(response)
    return response.text


def run_chat() -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    print("会話を開始します。終了するには「終了」または exit を入力してください。")

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

        response = chat.send_message(question)
        _print_usage(response)
        print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="会話履歴を保って、終了するまで続けて質問する",
    )
    args = parser.parse_args()

    if args.interactive:
        if args.question is not None:
            parser.error("--interactive と質問の位置引数は同時に指定できません")

    print(f"[model] {MODEL}")
    if args.interactive:
        try:
            run_chat()
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)
        return

    question = args.question if args.question is not None else DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
