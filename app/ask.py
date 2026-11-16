"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""
"""第一回宿題（実装）で追加：チャットモード機能（会話履歴を保ったまま質問できるモード）

使い方:
    1. --chat オプションをつけると、チャットモードが開始され、その時点から会話履歴の保持がスタートする
    2. /exit を入力すると、チャットモードを終了する

    （※チャットモード中に、独立した単発質問は行えない）

    uv run python -m app.ask --chat "LoRAとは何ですか？"
    uv run python -m app.ask --chat        # 質問を省略すると、まっさらな状態でチャットモードが開始される（講座に固有の質問はしない）
"""
import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())

    start = time.perf_counter()
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config={"temperature": 0.0},
    )
    elapsed = time.perf_counter() - start
    print(f"[応答時間] {elapsed:.2f} 秒")


    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[tokens] input: {usage.prompt_token_count}, "
            f"output: {usage.candidates_token_count}"
        )

    return response.text

def run_chat(initial_question: str | None = None) -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(
        model=MODEL,
        config={"temperature": 0.0},
    )

    question = initial_question
    print("終了するには /exit を入力してください。")

    while True:
        if question is None:
            question = input("\n質問> ").strip()

        if question == "/exit":
            break
        if not question:
            question = None
            continue

        start = time.perf_counter()
        response = chat.send_message(question)
        elapsed = time.perf_counter() - start
        print(f"[応答時間] {elapsed:.2f} 秒")
        print(response.text or "")

        usage = response.usage_metadata
        if usage is not None:
            print(
                f"[tokens] input: {usage.prompt_token_count}, "
                f"output: {usage.candidates_token_count}"
            )

        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", help="質問、または会話の最初の質問")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保って続けて質問する",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            run_chat(args.question)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
