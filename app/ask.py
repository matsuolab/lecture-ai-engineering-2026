"""第1回: Gemini に質問し、応答時間やトークン数を確認するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --model gemini-2.5-flash --model gemini-3.5-flash "LoRAとは？"
    uv run python -m app.ask --questions "LoRAとは？" "RAGとは？" --model gemini-2.5-flash
    uv run python -m app.ask --temperature 0.2 1.0 "LoRAとは？"
    uv run python -m app.ask --interactive --model gemini-2.5-flash

複数モデルを指定すると、各質問をすべてのモデルに送る。
対話モードでは、モデルごとに独立した会話履歴を保つ。
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
DEFAULT_TEMPERATURES = (0.2, 1.0)


def ask(
    question: str,
    model: str = MODEL,
    temperature: float = DEFAULT_TEMPERATURES[0],
    chat=None,
) -> str:
    if chat is None:
        client = genai.Client(api_key=get_api_key())
        started_at = time.perf_counter()
        response = client.models.generate_content(
            model=model,
            contents=question,
            config={"temperature": temperature},
        )
    else:
        started_at = time.perf_counter()
        response = chat.send_message(question)
    elapsed = time.perf_counter() - started_at
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else "不明"
    output_tokens = usage.candidates_token_count if usage else "不明"
    print(f"[temperature] {temperature}")
    print(f"[usage] 入力トークン数: {input_tokens}, 出力トークン数: {output_tokens}")
    print(f"[time] 応答時間: {elapsed:.2f} 秒")

    return response.text


def compare(
    questions: list[str],
    models: list[str],
    temperatures: list[float] | tuple[float, ...] = DEFAULT_TEMPERATURES,
) -> None:
    for question in questions:
        print(f"\n[質問] {question}")
        for model in models:
            for temperature in temperatures:
                print(f"\n[model] {model}")
                print(ask(question, model=model, temperature=temperature))


def interactive(
    models: list[str],
    temperatures: list[float] | tuple[float, ...] = DEFAULT_TEMPERATURES,
) -> None:
    client = genai.Client(api_key=get_api_key())
    chats = {
        (model, temperature): client.chats.create(
            model=model,
            config={"temperature": temperature},
        )
        for model in models
        for temperature in temperatures
    }
    print("質問を入力してください。終了するには /exit を入力します。")

    while True:
        try:
            question = input("質問> ").strip()
        except EOFError:
            print()
            return
        if question.lower() in {"/exit", "/quit"}:
            return
        if not question:
            continue

        for (model, temperature), chat in chats.items():
            print(f"\n[model] {model}")
            print(ask(question, model=model, temperature=temperature, chat=chat))


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini に質問して応答を比較する")
    parser.add_argument("question", nargs="?", help="モデルに送る質問")
    parser.add_argument("--questions", nargs="+", help="比較する質問を複数指定")
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="使用モデル。複数回指定すると同じ質問を各モデルに送る",
    )
    parser.add_argument(
        "--temperature",
        nargs=2,
        type=float,
        default=DEFAULT_TEMPERATURES,
        metavar=("LOW", "HIGH"),
        help="比較する2つの temperature 値 (既定: 0.2 1.0)",
    )
    parser.add_argument("--interactive", action="store_true", help="会話履歴を保って対話する")
    args = parser.parse_args()

    if args.question and args.questions:
        parser.error("質問は位置引数または --questions のどちらかで指定してください")
    if args.interactive and (args.question or args.questions):
        parser.error("--interactive と質問の直接指定は併用できません")

    models = args.models or [MODEL]
    try:
        if args.interactive:
            interactive(models, args.temperature)
        else:
            questions = args.questions or [args.question or DEFAULT_QUESTION]
            compare(questions, models, args.temperature)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
