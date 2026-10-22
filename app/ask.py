import argparse
import time
from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key


DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


@dataclass
class Result:
    """1回のLLM呼び出し結果を保存するクラス"""

    model: str
    temperature: float
    question: str
    answer: str
    elapsed_time: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


def send_message(
    chat,
    model: str,
    temperature: float,
    question: str,
) -> Result:
    """質問を送り、回答・時間・トークン数を返す。"""

    start = time.perf_counter()

    response = chat.send_message(question)

    elapsed_time = time.perf_counter() - start

    usage = response.usage_metadata

    return Result(
        model=model,
        temperature=temperature,
        question=question,
        answer=response.text or "",
        elapsed_time=elapsed_time,
        input_tokens=usage.prompt_token_count or 0,
        output_tokens=usage.candidates_token_count or 0,
        total_tokens=usage.total_token_count or 0,
    )


def print_result(result: Result) -> None:
    """回答と計測結果を表示する。"""

    print("\n[回答]")
    print(result.answer)

    print("\n--- 計測結果 ---")
    print(f"[model] {result.model}")
    print(f"[temperature] {result.temperature}")
    print(f"[time] {result.elapsed_time:.3f} sec")
    print(f"[usage] input : {result.input_tokens}")
    print(f"[usage] output: {result.output_tokens}")
    print(f"[usage] total : {result.total_tokens}")
    print("----------------\n")


def interactive_mode(
    first_question: str,
    temperature: float,
) -> None:
    """
    会話履歴を保持した状態で連続して質問する。
    """

    client = genai.Client(api_key=get_api_key())

    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            temperature=temperature,
        ),
    )

    print(f"[model] {MODEL}")
    print(f"[temperature] {temperature}")
    print("会話モードを開始します。")
    print("終了する場合は exit / quit / q を入力してください。\n")

    question = first_question

    while True:
        if not question:
            question = input("You > ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("会話を終了します。")
            break

        if not question:
            continue

        print(f"\n[質問] {question}")

        try:
            result = send_message(
                chat,
                MODEL,
                temperature,
                question,
            )
            print_result(result)

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))

            if e.code == 429:
                print(
                    "\n[rate limit]"
                    "\nAPI のレート制限に達した可能性があります。"
                    "\nRPM、TPM、RPDなどを確認してください。\n"
                )

        question = ""


def benchmark(
    models: list[str],
    questions: list[str],
    temperatures: list[float],
) -> None:
    """
    モデル × temperature × 質問の全組み合わせを比較する。
    """

    client = genai.Client(api_key=get_api_key())

    results: list[Result] = []

    for model in models:
        for temperature in temperatures:
            for question in questions:
                print("=" * 70)
                print(f"[model] {model}")
                print(f"[temperature] {temperature}")
                print(f"[質問] {question}")

                # 条件ごとに新しいチャットを作成する。
                chat = client.chats.create(
                    model=model,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                    ),
                )

                try:
                    result = send_message(
                        chat,
                        model,
                        temperature,
                        question,
                    )

                    results.append(result)

                    print(f"[time] {result.elapsed_time:.3f} sec")
                    print(f"[input tokens]  {result.input_tokens}")
                    print(f"[output tokens] {result.output_tokens}")
                    print(f"[total tokens]  {result.total_tokens}")

                    print("\n[回答]")
                    print(result.answer)

                except errors.APIError as e:
                    print(api_error_message(e.code, e.message))

                    if e.code == 429:
                        print(
                            "[rate limit] "
                            "RPM / TPM / RPD 制限に"
                            "達した可能性があります。"
                        )

    print_benchmark_summary(results)


def print_benchmark_summary(results: list[Result]) -> None:
    """ベンチマーク結果を表形式で表示する。"""

    if not results:
        print("\n比較できる結果がありません。")
        return

    print("\n\n")
    print("=" * 120)
    print("ベンチマーク結果")
    print("=" * 120)

    header = (
        f"{'MODEL':<28}"
        f"{'TEMP':>8}"
        f"{'TIME(sec)':>12}"
        f"{'INPUT':>10}"
        f"{'OUTPUT':>10}"
        f"{'TOTAL':>10}"
        f"  QUESTION"
    )

    print(header)
    print("-" * 120)

    for result in results:
        print(
            f"{result.model:<28}"
            f"{result.temperature:>8.2f}"
            f"{result.elapsed_time:>12.3f}"
            f"{result.input_tokens:>10}"
            f"{result.output_tokens:>10}"
            f"{result.total_tokens:>10}"
            f"  {result.question}"
        )

    print("=" * 120)

    print("\nモデル・temperature ごとの平均")

    conditions = sorted(
        {
            (r.model, r.temperature)
            for r in results
        }
    )

    for model, temperature in conditions:
        condition_results = [
            r
            for r in results
            if r.model == model
            and r.temperature == temperature
        ]

        avg_time = sum(
            r.elapsed_time for r in condition_results
        ) / len(condition_results)

        avg_input = sum(
            r.input_tokens for r in condition_results
        ) / len(condition_results)

        avg_output = sum(
            r.output_tokens for r in condition_results
        ) / len(condition_results)

        avg_total = sum(
            r.total_tokens for r in condition_results
        ) / len(condition_results)

        print(f"\n{model} / temperature={temperature}")
        print(f"  平均応答時間       : {avg_time:.3f} sec")
        print(f"  平均入力トークン数 : {avg_input:.1f}")
        print(f"  平均出力トークン数 : {avg_output:.1f}")
        print(f"  平均総トークン数   : {avg_total:.1f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="会話履歴を保持したLLMチャットと性能比較"
    )

    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="最初の質問",
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="複数モデル・質問の比較を行う",
    )

    parser.add_argument(
        "--models",
        nargs="+",
        default=[MODEL],
        help="比較するモデル",
    )

    parser.add_argument(
        "--questions",
        nargs="+",
        help="比較する質問",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="通常の会話モードで使用するtemperature",
    )

    parser.add_argument(
        "--temperatures",
        nargs="+",
        type=float,
        help="ベンチマークで比較するtemperature",
    )

    args = parser.parse_args()

    if args.benchmark:
        questions = args.questions or [args.question]

        temperatures = (
            args.temperatures
            if args.temperatures
            else [args.temperature]
        )

        benchmark(
            args.models,
            questions,
            temperatures,
        )

    else:
        interactive_mode(
            args.question,
            args.temperature,
        )


if __name__ == "__main__":
    main()