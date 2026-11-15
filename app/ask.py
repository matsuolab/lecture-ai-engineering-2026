"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask -t 0       # temperature を指定して質問する
    uv run python -m app.ask -m gemini-2.5-pro   # モデルを指定して質問する

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


def print_usage(response: types.GenerateContentResponse) -> None:
    """response.usage_metadata から入力・出力トークン数を表示する"""
    usage = response.usage_metadata
    if usage is None:
        print("[tokens] 取得できませんでした")
        return

    # 値が返ってこない項目は None になるので 0 として扱う
    input_tokens = usage.prompt_token_count or 0
    output_tokens = usage.candidates_token_count or 0
    thinking_tokens = usage.thoughts_token_count or 0
    total_tokens = usage.total_token_count or 0

    print(f"[tokens] 入力: {input_tokens} / 出力: {output_tokens}", end="")
    if thinking_tokens:
        print(f" / 思考: {thinking_tokens}", end="")
    print(f" / 合計: {total_tokens}\n")


def ask(question: str, model: str = MODEL) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=model, contents=question)
    print_usage(response)
    return response.text


def ask_with_temperature(question: str, temperature: float, model: str = MODEL) -> str:
    """temperature を指定して素のLLMに1回だけ質問する"""
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=model,
        contents=question,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    print_usage(response)
    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=None,
        help="生成のランダムさ（0〜2）。省略時はモデルのデフォルト",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=MODEL,
        help=f"使うモデル名。省略時は app/config.py の MODEL（{MODEL}）",
    )
    args = parser.parse_args()

    print(f"[model] {args.model}")
    if args.temperature is not None:
        print(f"[temperature] {args.temperature}")
    print(f"[質問] {args.question}\n")
    try:
        if args.temperature is None:
            print(ask(args.question, args.model))
        else:
            print(ask_with_temperature(args.question, args.temperature, args.model))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()