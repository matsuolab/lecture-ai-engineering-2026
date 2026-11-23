"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って続けて質問する

ツールを使わない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
TEMPERATURE = 0.2


def _print_usage(response) -> None:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return

    prompt_tokens = getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(usage, "candidates_token_count", None)
    if prompt_tokens is None and output_tokens is None:
        return

    prompt_value = prompt_tokens if prompt_tokens is not None else "unknown"
    output_value = output_tokens if output_tokens is not None else "unknown"
    print(f"[usage] input: {prompt_value}, output: {output_value}")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(temperature=TEMPERATURE),
    )
    _print_usage(response)
    return response.text


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    try:
        conversation = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(temperature=TEMPERATURE),
        )
        print("会話モードです。終了するには /exit と入力してください。")
        while True:
            try:
                question = input("質問> ")
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\n会話を終了します。")
                break

            if question.strip().lower() in {"/exit", "exit", "quit"}:
                break
            if not question.strip():
                continue

            response = conversation.send_message(question)
            _print_usage(response)
            print(response.text)
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument(
        "question",
        nargs="?",
        help="質問（省略時は講座に固有の質問をする）",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保って続けて質問する",
    )
    args = parser.parse_args()
    if args.chat and args.question:
        parser.error("会話モードでは質問を指定せずに実行してください")

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            chat()
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
