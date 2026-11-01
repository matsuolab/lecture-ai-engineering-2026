"""第1回: 会話履歴を保ってLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問から会話を始める

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。続けて質問すると、前の会話も参照する。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


class _ChatSession:
    def __init__(self):
        self._client = genai.Client(api_key=get_api_key())
        self._chat = self._client.chats.create(model=MODEL)

    def send_message(self, question: str):
        return self._chat.send_message(question)


def create_chat():
    return _ChatSession()


def ask(question: str, chat=None) -> str:
    if chat is None:
        chat = create_chat()
    response = chat.send_message(question)

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else "不明"
    output_tokens = usage.candidates_token_count if usage else "不明"
    print(f"[usage] input={input_tokens} tokens, output={output_tokens} tokens")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        chat = create_chat()
        question = args.question or DEFAULT_QUESTION
        while True:
            print(f"[質問] {question}\n")
            print(ask(question, chat))
            try:
                question = input("次の質問（終了: exit / quit / 終了）> ").strip()
            except EOFError:
                break
            if question.lower() in {"exit", "quit", "終了"}:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
