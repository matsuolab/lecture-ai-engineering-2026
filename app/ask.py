"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive
    uv run python -m app.ask --interactive "LoRAとは何ですか？"

通常モードはツールも会話履歴も持たない「素の」呼び出し。
--interactive では会話履歴を保ち、続けて質問できる。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors
from google.genai.types import GenerateContentResponseUsageMetadata

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    _print_usage(response.usage_metadata)
    return response.text


def _print_usage(usage: GenerateContentResponseUsageMetadata | None) -> None:
    if usage is not None:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        input_display = input_tokens if input_tokens is not None else "不明"
        output_display = output_tokens if output_tokens is not None else "不明"
        print(f"[usage] input: {input_display} tokens, output: {output_display} tokens")


def interactive_chat(initial_question: str | None = None) -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    question = initial_question
    while True:
        if question is None:
            try:
                question = input("質問（終了: 空行 または /exit）> ").strip()
            except EOFError:
                print()
                return
            if not question or question == "/exit":
                return

        print(f"[質問] {question}\n")
        response = chat.send_message(question)
        _print_usage(response.usage_metadata)
        print(response.text)
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="会話履歴を保って続けて質問する（終了: 空行 または /exit）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.interactive:
            interactive_chat(args.question)
        else:
            question = args.question if args.question is not None else DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
