"""第1回: 素のLLMに会話履歴を保って質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問から開始

対話中は同じ Chat を使い続けるため、前の質問と回答が次の質問にも引き継がれる。
終了するには exit を入力するか、入力を閉じる（Ctrl-D）。

ツールは持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time #応答時間計測のためインポート

from google import genai
from google.genai.chats import Chat
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat: Chat, question: str) -> str:
    #  送信前の現在時刻を記録する
    start_time = time.time()
    response = chat.send_message(question)

    #　受信の現在時刻から、開始時刻を引いて経過時間（秒）を計算する
    elapsed_time = time.time() - start_time

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[usage] 応答時間: {elapsed_time:.2f}秒 | "
            f"[usage] 入力トークン数: {usage.prompt_token_count}, "
            f"出力トークン数: {usage.candidates_token_count}"
        )

    if response.text is None:
        raise RuntimeError("モデルからテキスト形式の回答がありませんでした。")
    return response.text


def read_question() -> str | None:
    while True:
        try:
            question = input("\n次の質問（終了するには exit）> ").strip()
        except EOFError:
            return None
        if question.lower() in {"exit", "quit"}:
            return None
        if question:
            return question


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保って素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    question = args.question

    try:
        while True:
            print(f"[質問] {question}\n")
            print(ask(chat, question))
            next_question = read_question()
            if next_question is None:
                break
            question = next_question
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
