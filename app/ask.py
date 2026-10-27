"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

会話履歴は data/chat_history.json に保存され、次回実行時にも引き継がれる。
履歴を消して新しく始めるには、このファイルを削除する。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import json
import time
from pathlib import Path

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
HISTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "chat_history.json"


def load_history(path: Path) -> list[types.Content]:
    if not path.exists():
        return []

    messages = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(messages, list):
        raise ValueError("会話履歴の形式が正しくありません。JSON配列が必要です。")

    history = []
    for message in messages:
        if (
            not isinstance(message, dict)
            or message.get("role") not in {"user", "model"}
            or not isinstance(message.get("text"), str)
        ):
            raise ValueError("会話履歴の形式が正しくありません。role と text を確認してください。")
        history.append(
            types.Content(
                role=message["role"],
                parts=[types.Part(text=message["text"])],
            )
        )
    return history


def save_history(path: Path, history: list[types.Content]) -> None:
    messages = [
        {
            "role": message.role,
            "text": "".join(part.text or "" for part in message.parts),
        }
        for message in history
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def ask(question: str, history_path: Path = HISTORY_PATH) -> str:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(
        model=MODEL,
        history=load_history(history_path),
        config=types.GenerateContentConfig(temperature=2.0),
    )
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed_seconds = time.perf_counter() - started_at
    print(f"[応答時間] {elapsed_seconds:.2f}秒")
    save_history(history_path, chat.get_history())

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[tokens] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[履歴] {HISTORY_PATH}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    except (OSError, ValueError) as e:
        print(f"会話履歴を読み書きできません: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
