"""第1回: 会話履歴を保存しながら素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

会話履歴は .ask_history.json に保存され、次回実行時にも引き継がれる。
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

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
HISTORY_FILE = Path(__file__).resolve().parent.parent / ".ask_history.json"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())

    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            raise ValueError(f"{HISTORY_FILE} の形式が正しくありません（配列が必要です）")
    else:
        history = []

    user_turn = {"role": "user", "parts": [{"text": question}]}
    response = client.models.generate_content(
        model=MODEL,
        contents=[*history, user_turn],
    )

    answer = response.text
    if answer is None:
        raise RuntimeError("LLMから回答テキストが返されませんでした")

    history.extend([
        user_turn,
        {"role": "model", "parts": [{"text": answer}]},
    ])
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
