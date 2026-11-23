"""第1回: 会話履歴を保ちながら素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    # 質問後は続けて入力できる。終了するには exit を入力する。

ツールは持たないが、同じチャット内の会話履歴を保つ「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat():
    client = genai.Client(api_key=get_api_key())
    return client, client.chats.create(model=MODEL)


def ask(question: str, chat=None) -> str:
    if chat is None:
        client, chat = create_chat()
    response = chat.send_message(question)
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage and usage.prompt_token_count is not None else "不明"
    output_tokens = usage.candidates_token_count if usage and usage.candidates_token_count is not None else "不明"
    print(f"[トークン] 入力: {input_tokens} / 出力: {output_tokens}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        client, chat = create_chat()
        print(ask(args.question, chat))
        while True:
            try:
                question = input("\n次の質問 (終了: exit): ").strip()
            except EOFError:
                break
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue
            print(f"\n[質問] {question}\n")
            print(ask(question, chat))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
