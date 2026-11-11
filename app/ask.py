"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 会話モード（空行または /exit で終了）
    uv run python -m app.ask --interactive "LoRAとは何ですか？"

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors
from google.genai.chats import Chat
from google.genai.types import GenerateContentResponse

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_token_usage(response: GenerateContentResponse) -> None:
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    input_display = input_tokens if input_tokens is not None else "不明"
    output_display = output_tokens if output_tokens is not None else "不明"
    print(f"[tokens] 入力: {input_display}, 出力: {output_display}")


def ask(question: str) -> str | None:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_token_usage(response)

    return response.text


def ask_in_chat(question: str, chat: Chat) -> str | None:
    response = chat.send_message(question)
    print_token_usage(response)

    return response.text


def run_chat(chat: Chat, first_question: str | None = None) -> None:
    if first_question:
        print(f"[質問] {first_question}\n")
        print(ask_in_chat(first_question, chat))

    print("会話モードです。空行または /exit で終了します。")
    while True:
        try:
            question = input("質問> ").strip()
        except EOFError:
            print()
            break
        if not question or question == "/exit":
            break

        print()
        print(ask_in_chat(question, chat))


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="質問を指定した場合も、回答後に会話を続ける",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.question is None or args.interactive:
            client = genai.Client(api_key=get_api_key())
            chat = client.chats.create(model=MODEL)
            run_chat(chat, args.question)
        else:
            print(f"[質問] {args.question}\n")
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
