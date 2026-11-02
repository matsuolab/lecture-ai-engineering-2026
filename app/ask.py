"""第1回: 会話履歴を保ちながらLLMに質問するスクリプト。

使い方:
    

    uv run python -m app.ask            # 講座に固有の質問から会話を始める

ツールは使わず、同じチャットの会話履歴を引き継いで質問する。
講座に固有のことを聞くと、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。終了するには q と入力する。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat=None) -> str:
    if chat is None:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン] 入力: {usage.prompt_token_count} / "
            f"出力: {usage.candidates_token_count}"
        )
    else:
        print("[トークン] 使用量を取得できませんでした")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保ってLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(ask(question, chat))
            try:
                question = input("\n次の質問（終了するには q）> ").strip()
            except EOFError:
                break
            if question.lower() in {"q", "quit", "exit"}:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
