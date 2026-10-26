
"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"

temperatureの変更:
    AIE_TEMPERATURE=0.0 uv run python -m app.ask "LoRAとは何ですか？"
    AIE_TEMPERATURE=1.0 uv run python -m app.ask "LoRAとは何ですか？"
"""

import argparse
import os

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    # Gemini APIクライアント
    client = genai.Client(api_key=get_api_key())

    # temperatureを環境変数から取得
    temperature = float(os.getenv("AIE_TEMPERATURE", "0.0"))

    # Gemini APIを呼び出す
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=genai.types.GenerateContentConfig(
            temperature=temperature
        ),
    )

    # トークン使用量を取得
    usage = response.usage_metadata

    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")
        print(f"[合計トークン数] {usage.total_token_count}")
        print()

    return response.text or ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="素のLLMに質問する"
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[temperature] {os.getenv('AIE_TEMPERATURE', '0.0')}")
    print(f"[質問] {args.question}\n")

    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
