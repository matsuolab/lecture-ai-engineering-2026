"""第1回: 会話履歴を保ちながらLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --reset-history  # 会話履歴を消去する

1回の起動につき1つ質問し、会話履歴は .ask_history.json に保存する。
ツールは使わない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import json
from pathlib import Path

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
HISTORY_PATH = Path(__file__).resolve().parent.parent / ".ask_history.json"


def load_history() -> list[types.Content]:
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open(encoding="utf-8") as history_file:
        return [types.Content.model_validate(item) for item in json.load(history_file)]


def save_history(history: list[types.Content]) -> None:
    temporary_path = HISTORY_PATH.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as history_file:
        json.dump(
            [item.model_dump(mode="json", by_alias=True, exclude_none=True) for item in history],
            history_file,
            ensure_ascii=False,
            indent=2,
        )
        history_file.write("\n")
    temporary_path.replace(HISTORY_PATH)


def ask(chat, question: str) -> str:
    response = chat.send_message(question)

    # 入力トークン数と出力トークン数を表示
    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[usage] input={usage.prompt_token_count} tokens, "
            f"output={usage.candidates_token_count} tokens"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--reset-history", action="store_true", help="保存した会話履歴を消去する")
    args = parser.parse_args()

    if args.reset_history:
        HISTORY_PATH.unlink(missing_ok=True)
        print("[history] cleared")
        return

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        history = load_history()
        chat = client.chats.create(model=MODEL, history=history)
        print(f"[質問] {args.question}\n")
        print(ask(chat, args.question))
        save_history(chat.get_history())
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
