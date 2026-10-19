"""第1回: 会話履歴を保ちながらLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールは使わず、同じセッション内の会話履歴を保つ「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
LOG_PATH = Path("learning_log/ask.jsonl")


def ask(chat, question: str) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    if usage is not None:
        print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "answer": response.text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }, ensure_ascii=False) + "\n")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保ちながらLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[ログ] {LOG_PATH}")
    question = args.question
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)

        while True:
            if question is None:
                question = input("\n[質問] (終了: /exit) ")
            if question.strip().lower() in {"/exit", "exit", "終了"}:
                break
            if not question.strip():
                question = None
                continue

            print(f"[質問] {question}\n")
            print(ask(chat, question))
            question = None
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
