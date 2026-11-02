"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    AIE_TEMPERATURE=0.2 uv run python -m app.ask "LoRAとは何ですか？"
"""

import argparse
import os

from google import genai
from google.genai import errors
from google.genai import types  # types をインポート

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    
    # 環境変数 AIE_TEMPERATURE から取得（デフォルトは 1.0 または指定なし）
    # コマンドライン引数で渡したい場合は argparse から引数を受け取るよう変更してください
    temp_env = os.getenv("AIE_TEMPERATURE")
    gen_config = None
    if temp_env is not None:
        gen_config = types.GenerateContentConfig(temperature=float(temp_env))

    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=gen_config,  # temperature 設定を適用
    )

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[tokens] input={usage.prompt_token_count} "
            f"output={usage.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    # 表示ログに temperature も出力するようにしておくと実験時に便利です
    temp_env = os.getenv("AIE_TEMPERATURE", "default")
    print(f"[model] {MODEL}")
    print(f"[temperature] {temp_env}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
