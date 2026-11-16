"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って続けて質問する

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(usage) -> None:
    if usage is None:
        print("[tokens] 使用量を取得できませんでした")
    else:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        print(f"[tokens] 入力: {input_tokens if input_tokens is not None else '不明'} / 出力: {output_tokens if output_tokens is not None else '不明'}")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response.usage_metadata)
    return response.text


def chat() -> None:
    """会話履歴を自分で持ち、毎回まとめて送る。"""
    client = genai.Client(api_key=get_api_key())
    history = []  # ここが「記憶」の正体

    print(f"[model] {MODEL}")
    print("会話モード（空Enter・exit・quit で終了）")

    while True:
        try:
            question = input("\nあなた> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question in ("", "exit", "quit"):
            break

        # 1. ユーザー発言を履歴に追加
        history.append(types.Content(role="user", parts=[types.Part(text=question)]))

        try:
            # 2. 履歴を全部まとめて送る
            response = client.models.generate_content(model=MODEL, contents=history)
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            history.pop()  # 失敗した質問は履歴から外す
            continue

        answer = response.text or ""

        # 3. モデルの回答も履歴に追加（これがないと文脈が切れる）
        history.append(types.Content(role="model", parts=[types.Part(text=answer)]))

        print(f"\nAI> {answer}\n")
        print_usage(response.usage_metadata)
        print(f"[履歴] {len(history)} 件")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保って続けて質問する")
    args = parser.parse_args()

    if args.chat:
        chat()
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