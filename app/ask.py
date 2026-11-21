"""第1回: 素のLLMに会話形式で質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問から会話を始める

追加の質問は同じ会話履歴を使って送信し、空Enterで終了する。
ツールは持たない「素の」呼び出し。
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


def ask(question: str, chat=None) -> str:
    if chat is None:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 入力: 取得不可, 出力: 取得不可")
    else:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        input_display = input_tokens if input_tokens is not None else "取得不可"
        output_display = output_tokens if output_tokens is not None else "取得不可"
        print(f"[トークン数] 入力: {input_display}, 出力: {output_display}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        question = args.question
        while question:
            print(f"[質問] {question}\n")
            print(ask(question, chat))
            try:
                question = input("\n続けて質問してください（終了するには空Enter）: ").strip()
            except EOFError:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
