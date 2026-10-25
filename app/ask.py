"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --temperature 0 "LoRAとは何ですか？"
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（空行か exit で終了）

ツールを持たない「素の」呼び出し。
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


def make_config(temperature: float | None) -> types.GenerateContentConfig | None:
    """temperature を指定したときだけ config を作る（省略時はモデルの既定値）。"""
    if temperature is None:
        return None
    return types.GenerateContentConfig(temperature=temperature)


def print_usage(response: types.GenerateContentResponse) -> None:
    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")


def ask(question: str, temperature: float | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL, contents=question, config=make_config(temperature)
    )
    print_usage(response)
    return response.text


def chat_loop(first_question: str | None = None, temperature: float | None = None) -> None:
    """会話履歴を保ったまま、続けて質問する。空行・exit・Ctrl+D で終了。"""
    client = genai.Client(api_key=get_api_key())
    # chat オブジェクトが履歴を持ち、send_message のたびに過去のやり取りも一緒に送る
    chat = client.chats.create(model=MODEL, config=make_config(temperature))

    question = first_question
    while True:
        if question is None:
            try:
                question = input("\n[質問] ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if question in ("", "exit", "quit"):
                break
        try:
            response = chat.send_message(question)
        except errors.APIError as e:
            # エラーでも会話は終わらせず、次の質問を待つ
            print(api_error_message(e.code, e.message))
        else:
            print_usage(response)
            print(response.text)
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--temperature", type=float, default=None, help="0.0〜2.0。省略時はモデルの既定値")
    parser.add_argument("--chat", action="store_true", help="会話履歴を保ったまま続けて質問する")
    args = parser.parse_args()

    temp_label = args.temperature if args.temperature is not None else "既定"
    print(f"[model] {MODEL}  [temperature] {temp_label}")

    if args.chat:
        print("[会話モード] 空行か exit で終了")
        chat_loop(args.question, args.temperature)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question, args.temperature))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
