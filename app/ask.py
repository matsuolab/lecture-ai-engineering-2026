"""第1回: 素のLLMに会話しながら質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 講座に固有の質問の後、続けて質問できる

ツールは持たず、同じチャットの会話履歴を使って質問に答える「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time
from typing import Any, Callable

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat: Any) -> str:
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed_seconds = time.perf_counter() - started_at
    print(f"[timing] response_seconds={elapsed_seconds:.3f}")

    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        if input_tokens is not None or output_tokens is not None:
            print(f"[usage] input_tokens={input_tokens}, output_tokens={output_tokens}")

    return response.text


def run_conversation(
    chat: Any,
    first_question: str,
    input_fn: Callable[[str], str] = input,
) -> None:
    question = first_question
    while True:
        print(f"[質問] {question}\n")
        print(ask(question, chat))
        try:
            question = input_fn("\n質問（終了するには exit）> ").strip()
        except EOFError:
            break
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        run_conversation(chat, args.question)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()