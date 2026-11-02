"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
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


def ask(chat, question: str) -> str:
    response = chat.send_message(question)
   
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    print(f"[tokens] 入力: {input_tokens if input_tokens is not None else '不明'}")
    print(f"[tokens] 出力: {output_tokens if output_tokens is not None else '不明'}")

    return response.text or ""


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")

    question = args.question  # 追加
    while True:  # 追加：繰り返し処理
        try:
            print(ask(chat, question))  # 変更：chatを渡す
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        question = input("質問 > ").strip()  # 追加：次の質問を入力

        if question.lower() in ("exit", "quit"):  # 追加
            break

        if not question:  # 追加：空入力を無視
            continue
    


if __name__ == "__main__":
    main()
