"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --interactive
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

会話履歴を保持して、続けて質問することもできる。
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


def _history_to_contents(history):
    if not history:
        return []

    contents = []
    for item in history:
        if isinstance(item, dict):
            contents.append(item)
            continue
        if isinstance(item, tuple) and len(item) == 2:
            role, text = item
            contents.append({"role": role, "parts": [{"text": str(text)}]})
            continue
        if isinstance(item, str):
            contents.append({"role": "user", "parts": [{"text": item}]})
            continue
        contents.append({"role": "user", "parts": [{"text": str(item)}]})
    return contents


def ask(question: str, history=None) -> str:
    client = genai.Client(api_key=get_api_key())

    if history:
        contents = _history_to_contents(history)
        contents.append({"role": "user", "parts": [{"text": question}]})
    else:
        contents = question

    response = client.models.generate_content(model=MODEL, contents=contents)

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(usage, "candidates_token_count", None)

    if prompt_tokens is not None:
        print(f"[入力トークン数] {prompt_tokens}")
    if output_tokens is not None:
        print(f"[出力トークン数] {output_tokens}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="会話履歴を保ちながら質問を続ける",
    )
    args = parser.parse_args()

    if args.interactive:
        history = []
        while True:
            try:
                question = input("Q> ")
            except EOFError:
                print()
                break

            if not question.strip():
                continue
            if question.strip().lower() in {"exit", "quit", "q"}:
                break

            print(f"[model] {MODEL}")
            print(f"[質問] {question}\n")
            try:
                answer = ask(question, history=history)
                history.append({"role": "user", "parts": [{"text": question}]})
                history.append({"role": "model", "parts": [{"text": answer}]})
                print(answer)
            except errors.APIError as e:
                print(api_error_message(e.code, e.message))
                raise SystemExit(1)
            print()
        return

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
