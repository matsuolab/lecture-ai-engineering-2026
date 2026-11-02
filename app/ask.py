"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って対話する

通常モードはツールも会話履歴も持たない「素の」呼び出し。
--chat モードでは、起動中の会話履歴を使って続けて質問できる。
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


def print_usage(response) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 使用量情報を取得できませんでした")
    else:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        input_display = input_tokens if input_tokens is not None else "不明"
        output_display = output_tokens if output_tokens is not None else "不明"
        print(f"[トークン数] 入力: {input_display} / 出力: {output_display}")


def ask(question: str, chat=None) -> str:
    started_at = time.perf_counter()

    if chat is None:
        client = genai.Client(api_key=get_api_key())
        response = client.models.generate_content(
            model=MODEL,
            contents=question,
            config={"temperature": 1.0},
        )
    else:
        response = chat.send_message(question)

    elapsed = time.perf_counter() - started_at
    print(f'[応答時間] {elapsed:.2f}秒')
    print_usage(response)
    return response.text


def run_chat() -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL, config={"temperature": 1.0})
    print("会話を始めます。終了するには /exit または /quit を入力してください。")

    while True:
        try:
            question = input("あなた: ").strip()
        except EOFError:
            print()
            break

        if question.lower() in {"/exit", "/quit"}:
            break
        if not question:
            continue

        print(f"[質問] {question}\n")
        print(ask(question, chat))
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保って対話する（/exit または /quit で終了）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            run_chat()
        else:
            print(f"[質問] {args.question}\n")
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
