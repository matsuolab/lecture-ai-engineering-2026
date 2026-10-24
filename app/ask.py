"""第1回: 素のLLMに会話履歴を保って質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールは使わない「素の」呼び出し。終了するには exit、quit、終了 のいずれかを入力する。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors, types
from google.genai.chats import Chat

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
TEMPERATURE = 0.1


def ask(chat: Chat, question: str) -> str:
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed = time.perf_counter() - started_at

    print(f"[応答時間] {elapsed:.2f}秒")
    usage = response.usage_metadata
    print(f"[入力トークン] {usage.prompt_token_count}")
    print(f"[出力トークン] {usage.candidates_token_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保って素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[temperature] {TEMPERATURE}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(temperature=TEMPERATURE),
        )

        question = args.question
        while True:
            print(f"\n[質問] {question}\n")
            print(ask(chat, question))
            try:
                question = input("\n続けて質問できます（終了: exit / quit / 終了）> ").strip()
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\n会話を終了します。")
                break

            if question.lower() in {"exit", "quit", "終了"}:
                print("会話を終了します。")
                break
            if not question:
                continue
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
