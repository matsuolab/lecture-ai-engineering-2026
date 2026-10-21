"""第1回: 素のLLMに会話履歴を保って質問するスクリプト。

使い方:
    uv run python -m app.ask
    # コマンド実行後に最初の質問を入力する。回答後に次の質問を入力し、空行で終了。

ツールは持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from time import perf_counter

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key


def ask(chat, question: str) -> str:
    started_at = perf_counter()
    response = chat.send_message(question)
    elapsed = perf_counter() - started_at
    print(f"[timing] response_time_seconds={elapsed:.2f}")

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[usage] input_tokens={usage.prompt_token_count} "
            f"output_tokens={usage.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保って素のLLMに質問する")
    parser.add_argument("question", nargs="?", help="最初の質問（省略時は起動後に入力）")
    args = parser.parse_args()

    question = args.question
    if question is None:
        try:
            question = input("最初の質問: ").strip()
        except EOFError:
            return
    if not question:
        return

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        while True:
            print(ask(chat, question))
            try:
                question = input("\n次の質問 (空行で終了): ").strip()
            except EOFError:
                break
            if not question:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
