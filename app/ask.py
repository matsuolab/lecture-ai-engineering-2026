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
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
DEFAULT_HISTORY_FILE = Path(".ask_history.txt")
MAX_HISTORY_TURNS = 3


def load_history(history_file: Path | None = None) -> list[str]:
    path = history_file or DEFAULT_HISTORY_FILE
    if not path.exists():
        return []
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def keep_recent_history(history: list[str], max_turns: int = MAX_HISTORY_TURNS) -> list[str]:
    """直近の数往復だけ残して、古い履歴を捨てる。"""
    if max_turns <= 0:
        return []
    return history[-(max_turns * 2) :]


def save_history(history: list[str], history_file: Path | None = None) -> None:
    path = history_file or DEFAULT_HISTORY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    trimmed = keep_recent_history(history)
    path.write_text("\n".join(trimmed) + "\n", encoding="utf-8")


def _build_contents(question: str, history: list[str] | None = None) -> str:
    if not history:
        return question

    previous = "\n\n".join(line.strip() for line in history if line and line.strip())
    if not previous:
        return question
    return (
        "以下は過去の会話履歴です。前のやり取りを踏まえて、最後の質問に答えてください。\n\n"
        f"{previous}\n\n"
        f"ユーザー: {question}\n"
        "アシスタント:"
    )


def ask(question: str, history: list[str] | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    contents = _build_contents(question, history)
    response = client.models.generate_content(model=MODEL, contents=contents)

    usage = getattr(response, "usage_metadata", None)
    input_tokens = getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(usage, "candidates_token_count", None)

    if input_tokens is not None:
        print(f"[input_tokens] {input_tokens}")
    if output_tokens is not None:
        print(f"[output_tokens] {output_tokens}")

    return response.text


def main_for_test(question: str, history_file: Path | None = None, reset_history: bool = False) -> str:
    path = history_file or DEFAULT_HISTORY_FILE
    history = []
    if not reset_history and path.exists():
        history = load_history(path)
    history = keep_recent_history(history)

    print(f"[model] {MODEL}")
    print(f"[質問] {question}\n")
    try:
        answer = ask(question, history=history)
        history.extend([f"ユーザー: {question}", f"アシスタント: {answer}"])
        save_history(history, path)
        print(answer)
        return answer
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--history-file", type=Path, help="会話履歴を保存するファイルパス")
    parser.add_argument(
        "--reset-history",
        action="store_true",
        help="履歴ファイルを削除して会話を最初からやり直す（通常は使わない）",
    )
    args = parser.parse_args()

    history_file = args.history_file or DEFAULT_HISTORY_FILE
    if args.reset_history and history_file.exists():
        history_file.unlink()

    main_for_test(question=args.question, history_file=history_file, reset_history=args.reset_history)


if __name__ == "__main__":
    main()
