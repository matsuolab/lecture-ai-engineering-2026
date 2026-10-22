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

    print_usage(response)

    return response.text


def print_usage(response) -> None:
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    print(f"[トークン] 入力: {input_tokens}, 出力: {output_tokens}")


def chat(initial_question: str | None = None) -> None:
    client = genai.Client(api_key=get_api_key())
    conversation = client.chats.create(model=MODEL)
    question = initial_question

    while True:
        if question is None:
            try:
                question = input("質問 (exit/quit で終了): ").strip()
            except EOFError:
                break
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            response = conversation.send_message(question)
            print(response.text)
            print_usage(response)
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--chat", action="store_true", help="会話履歴を保って続けて質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            if args.question:
                print(f"[質問] {args.question}\n")
            chat(args.question)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
