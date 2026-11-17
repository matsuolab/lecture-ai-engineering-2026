"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --temperature 0.7 "LoRAとは何ですか？"

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
同じ条件で3回実行し、モデルや temperature を変えたときの回答の違いを比べられる。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
DEFAULT_REPEAT = 3


def ask(question: str, temperature: float | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    if temperature is None:
        response = client.models.generate_content(model=MODEL, contents=question)
    else:
        response = client.models.generate_content(
            model=MODEL,
            contents=question,
            config=types.GenerateContentConfig(temperature=temperature),
        )

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return response.text


def positive_int(value: str) -> int:
    """argparse 用に1以上の整数を検証する。"""
    try:
        number = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("1以上の整数を指定してください") from e
    if number < 1:
        raise argparse.ArgumentTypeError("1以上の整数を指定してください")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する（既定で3回実行）")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--repeat", type=positive_int, default=DEFAULT_REPEAT)
    parser.add_argument("--temperature", type=float)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    temperature_label = (
        str(args.temperature) if args.temperature is not None else "モデル既定"
    )
    print(f"[temperature] {temperature_label}")
    print(f"[質問] {args.question}\n")
    try:
        for run in range(1, args.repeat + 1):
            print(f"[回答 {run}/{args.repeat}]")
            print(ask(args.question, temperature=args.temperature))
            if run < args.repeat:
                print()
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
