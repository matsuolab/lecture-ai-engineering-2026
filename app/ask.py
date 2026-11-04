"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 会話モード。exit または quit で終了

会話モードでは履歴を保ったまま続けて質問できる。
ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def _ask_with_history(
    client: genai.Client,
    question: str,
    history: list[types.Content],
) -> tuple[str, float, int | None, int | None, int | None]:
    user_turn = types.Content(role="user", parts=[types.Part(text=question)])
    started_at = time.perf_counter()
    response = client.models.generate_content(
        model=MODEL,
        contents=[*history, user_turn],
    )
    elapsed_seconds = time.perf_counter() - started_at

    answer = response.text
    if answer is None:
        raise RuntimeError("モデルからテキスト形式の回答が返りませんでした。")

    history.extend(
        [
            user_turn,
            types.Content(role="model", parts=[types.Part(text=answer)]),
        ]
    )
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    total_tokens = usage.total_token_count if usage else None
    return answer, elapsed_seconds, input_tokens, output_tokens, total_tokens


def ask(question: str) -> str:
    """履歴を使わずに1回だけ質問する（既存の呼び出し向け）。"""
    client = genai.Client(api_key=get_api_key())
    answer, _, _, _, _ = _ask_with_history(client, question, [])
    return answer


def _print_metrics(
    elapsed_seconds: float,
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
) -> None:
    def display(value: int | None) -> str:
        return str(value) if value is not None else "取得不可"

    print(f"[応答時間] {elapsed_seconds:.2f} 秒")
    print(
        "[トークン数] "
        f"入力: {display(input_tokens)}, "
        f"出力: {display(output_tokens)}, "
        f"合計: {display(total_tokens)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    history: list[types.Content] = []
    try:
        client = genai.Client(api_key=get_api_key())
        if args.question is not None:
            print(f"[質問] {args.question}\n")
            answer, elapsed, input_tokens, output_tokens, total_tokens = (
                _ask_with_history(client, args.question, history)
            )
            print(answer)
            _print_metrics(elapsed, input_tokens, output_tokens, total_tokens)
            return

        print("会話モードです。終了するには exit または quit を入力してください。")
        while True:
            try:
                question = input("\n質問> ").strip()
            except EOFError:
                print()
                break
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue

            answer, elapsed, input_tokens, output_tokens, total_tokens = (
                _ask_with_history(client, question, history)
            )
            print(f"\n{answer}")
            _print_metrics(elapsed, input_tokens, output_tokens, total_tokens)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
