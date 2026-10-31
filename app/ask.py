"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive  # 会話を続ける

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time
from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, model: str = MODEL) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=model, contents=question)

    print_usage(response)

    return response.text


def print_usage(response) -> None:
    """入力トークン数と出力トークン数の計算"""
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage and usage.prompt_token_count is not None else "不明"
    output_tokens = usage.candidates_token_count if usage and usage.candidates_token_count is not None else "不明"
    print(f"[tokens] input: {input_tokens}, output: {output_tokens}")


def send_chat_message(chat, question: str) -> None:
    """質問を受け取ってから回答を表示するまでの時間を計算する"""
    started_at = time.perf_counter()
    response = chat.send_message(question)

    print_usage(response)
    print(response.text)
    elapsed = time.perf_counter() - started_at
    print(f"[response time] {elapsed:.2f} s")


def interactive_chat(initial_question: str | None = None, model: str = MODEL) -> None:
    """前の会話を保存した状態で会話を進める"""
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=model)

    if initial_question:
        send_chat_message(chat, initial_question)

    print("質問を入力してください（終了: :q または Ctrl-D）")
    while True:
        try:
            question = input("質問> ").strip()
        except EOFError:
            print()
            break
        if question == ":q":
            break
        if not question:
            continue

        send_chat_message(chat, question)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--interactive", action="store_true", help="会話履歴を保って質問を続ける")
    parser.add_argument("--model", choices=['gemini-3.5-flash', 'gemini-3.6-flash', 'gemini-3.8-flash'], default=MODEL)
    args = parser.parse_args()

    print(f"[model] {args.model}")
    try:
        if args.interactive:
            interactive_chat(args.question, args.model)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            started_at = time.perf_counter()
            answer = ask(question, args.model)
            print(answer)
            elapsed = time.perf_counter() - started_at
            print(f"[response time] {elapsed:.2f} s")
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
