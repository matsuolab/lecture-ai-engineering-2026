"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"

    # temperatureを変更する場合
    AIE_TEMPERATURE=0.0 uv run python -m app.ask "LoRAとは何ですか？"
    AIE_TEMPERATURE=1.0 uv run python -m app.ask "LoRAとは何ですか？"

ツールも会話履歴も持たない「素の」呼び出し。
"""

import argparse
import os

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key


DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())

    # 環境変数からtemperatureを取得
    temperature = float(os.getenv("AIE_TEMPERATURE", "1.0"))

    # Gemini APIを呼び出す
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            temperature=temperature
        ),
    )

    # トークン数を取得
    usage = response.usage_metadata

    input_tokens = (
        usage.prompt_token_count
        if usage and usage.prompt_token_count is not None
        else "不明"
    )

    output_tokens = (
        usage.candidates_token_count
        if usage and usage.candidates_token_count is not None
        else "不明"
    )

    print(f"[temperature] {temperature}")
    print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")

    return response.text


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