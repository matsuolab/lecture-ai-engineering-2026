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
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, temperature: float = 0.2) -> str:
    client = genai.Client(api_key=get_api_key())

    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            temperature=temperature,
        ),
    )

    if response.usage_metadata:
        print(
            "[tokens] input="
            f"{response.usage_metadata.prompt_token_count} / "
            "output="
            f"{response.usage_metadata.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    if not 0.0 <= args.temperature <= 2.0:
        parser.error("--temperature は 0.0 から 2.0 の範囲で指定してください")

    print(f"[model] {MODEL}")
    print(f"[temperature] {args.temperature}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question, args.temperature))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
