"""第1回: 素のLLMに会話履歴を保って質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問から会話を始める

ツールは使わず、同じチャットセッションで会話履歴を保つ。
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
    answer = response.text

    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        print("[usage] 使用量情報を取得できませんでした")
    else:
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        print(
            f"[usage] 入力トークン数: {input_tokens}, "
            f"出力トークン数: {output_tokens}"
        )

    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保って質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(ask(chat, question))
            question = input("\n続けて質問してください (終了: 空行/exit): ").strip()
            if not question or question.lower() in {"exit", "quit", "終了"}:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    except EOFError:
        print()


if __name__ == "__main__":
    main()
