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


def ask(question: str, temperature: float | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    if temperature is None:
        response = client.models.generate_content(model=MODEL, contents=question)
    else:
        response = client.models.generate_content(
            model=MODEL,
            contents=question,
            config=genai.types.GenerateContentConfig(temperature=temperature),
        )

    usage = response.usage_metadata
    if usage is not None:
        print(
            "[トークン使用量] "
            f"入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}, "
            f"合計: {usage.total_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--temperature", type=float)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    temperature_label = (
        args.temperature if args.temperature is not None else "モデル既定値"
    )
    print(f"[temperature] {temperature_label}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question, temperature=args.temperature))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
