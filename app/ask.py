"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（宿題・実装）
    uv run python -m app.ask --chat "LoRAとは何ですか？"   # 最初の質問を指定して会話を始める

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from collections.abc import Callable

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

# 会話モードを終える入力
EXIT_WORDS = {"exit", "quit", "q", "終了"}


def print_usage(response: types.GenerateContentResponse) -> None:
    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[tokens] input={usage.prompt_token_count}, "
            f"output={usage.candidates_token_count}"
        )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response)
    return response.text


def run_chat(chat, first_question: str | None = None, read_line: Callable[[str], str] = input) -> None:
    """会話履歴を保ったまま、続けて質問する。

    chat は client.chats.create() で作るチャットセッション。send_message のたびに
    それまでの履歴（自分の質問とモデルの回答）がまとめて送られるので、
    「それ」「さっきの」のような前の発言を指す質問にも答えられる。
    その分、ターンが進むほど入力トークン数が増えていく。
    """
    question = first_question
    while True:
        if question is None:
            try:
                question = read_line("\n[あなた] ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
        if not question:
            question = None
            continue
        if question.lower() in EXIT_WORDS:
            break

        try:
            response = chat.send_message(question)
        except errors.APIError as e:
            # 失敗したターンは履歴に残らないので、待ってから同じ質問をやり直せる
            print(api_error_message(e.code, e.message))
        else:
            print_usage(response)
            print(f"[モデル] {response.text}")
        question = None

    print(f"[会話終了] 履歴のメッセージ数: {len(chat.get_history())}")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--chat", action="store_true", help="会話履歴を保ったまま続けて質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")

    if args.chat:
        print("会話モード（exit で終了）")
        client = genai.Client(api_key=get_api_key())
        run_chat(client.chats.create(model=MODEL), args.question)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
