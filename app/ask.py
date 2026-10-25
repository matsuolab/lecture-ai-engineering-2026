"""第1回: 会話履歴を保ちながらLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --temperature 0.2 "LoRAとは何ですか？"
    # 対話を終了するには、質問プロンプトで空行を入力する

会話履歴を保持して続けて質問できる。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors, types
from google.genai.chats import Chat

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat(client: genai.Client, temperature: float | None = None) -> Chat:
    config = (
        types.GenerateContentConfig(temperature=temperature)
        if temperature is not None
        else None
    )
    return client.chats.create(model=MODEL, config=config)


def ask(chat: Chat, question: str) -> str:
    started_at = time.perf_counter()
    response = chat.send_message(question)
    elapsed = time.perf_counter() - started_at
    print(f"[応答時間] {elapsed:.2f}秒")
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 入力: 不明 / 出力: 不明")
    else:
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        input_count = input_tokens if input_tokens is not None else "不明"
        output_count = output_tokens if output_tokens is not None else "不明"
        print(f"[トークン数] 入力: {input_count} / 出力: {output_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--temperature",
        type=float,
        help="生成のtemperature（省略時はモデル既定値）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    temperature_label = (
        args.temperature if args.temperature is not None else "モデル既定"
    )
    print(f"[temperature] {temperature_label}")
    print(f"[質問] {args.question}\n")
    try:
        with genai.Client(api_key=get_api_key()) as client:
            chat = create_chat(client, temperature=args.temperature)
            print(ask(chat, args.question))
            while True:
                try:
                    question = input("\n質問（空欄で終了）: ")
                except EOFError:
                    break
                if not question.strip():
                    break
                print(ask(chat, question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
