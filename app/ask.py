"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保って対話する

単発モードはツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
BENCHMARK_QUESTIONS = [
    "LoRAとは何ですか？",
    DEFAULT_QUESTION,
]


def print_usage(response, elapsed_seconds: float | None = None) -> None:
    if elapsed_seconds is not None:
        print(f"[応答時間] {elapsed_seconds:.2f}秒")
    usage = response.usage_metadata
    if usage is None:
        print("[usage] トークン使用量は取得できませんでした")
    else:
        print(f"[usage] 入力トークン数: {usage.prompt_token_count}")
        print(f"[usage] 出力トークン数: {usage.candidates_token_count}")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    started = time.perf_counter()
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response, time.perf_counter() - started)
    return response.text


def benchmark(models: list[str], questions: list[str]) -> None:
    client = genai.Client(api_key=get_api_key())
    for model in models:
        for question in questions:
            started = time.perf_counter()
            response = client.models.generate_content(model=model, contents=question)
            elapsed = time.perf_counter() - started
            print(f"\n[比較] model={model} / 質問={question}")
            print_usage(response, elapsed)
            print(f"[回答] {response.text}")


def chat(initial_question: str | None = None) -> None:
    client = genai.Client(api_key=get_api_key())
    conversation = client.chats.create(model=MODEL)
    print("対話モードです。終了するには 'exit' または '終了' と入力してください。")

    question = initial_question
    while True:
        if question is None:
            try:
                question = input("あなた: ").strip()
            except EOFError:
                break
            except KeyboardInterrupt:
                print()
                break

        if not question:
            question = None
            continue
        if question.casefold() in {"exit", "quit", "終了"}:
            break

        started = time.perf_counter()
        response = conversation.send_message(question)
        print_usage(response, time.perf_counter() - started)
        print(f"Gemini: {response.text}\n")
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する・応答を比較する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--chat", action="store_true", help="会話履歴を保って対話する")
    parser.add_argument("--benchmark", action="store_true", help="複数モデル・質問の応答時間とトークン数を比較する")
    parser.add_argument("--models", nargs="+", help="比較するモデル名（--benchmark と併用）")
    parser.add_argument(
        "--benchmark-questions",
        nargs="+",
        help="比較に使う質問（省略時は一般的な質問と講座固有の質問）",
    )
    args = parser.parse_args()

    if args.chat and args.benchmark:
        parser.error("--chat と --benchmark は同時に指定できません")
    if args.benchmark and args.question:
        parser.error("--benchmark では位置引数 question ではなく --benchmark-questions を指定してください")
    if args.benchmark and not args.models:
        parser.error("--benchmark には --models で比較するモデルを指定してください")
    if not args.benchmark and args.models:
        parser.error("--models は --benchmark と併用してください")
    if not args.benchmark and args.benchmark_questions:
        parser.error("--benchmark-questions は --benchmark と併用してください")

    print(f"[model] {MODEL}")
    try:
        if args.benchmark:
            benchmark(args.models, args.benchmark_questions or BENCHMARK_QUESTIONS)
        elif args.chat:
            chat(args.question)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
