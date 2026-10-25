"""第1回 発展: 複数の質問を複数モデルで比較するスクリプト。"""

from dataclasses import dataclass
from time import perf_counter

from google import genai
from google.genai import errors

from app.config import api_error_message, get_api_key

MODELS = ("gemini-3.8-flash", "gemini-3.5-flash-lite")


@dataclass(frozen=True)
class ComparisonResult:
    question: str
    model: str
    response_seconds: float
    output_tokens: int | None
    answer: str | None = None
    error: str | None = None


def compare_question(client: genai.Client, question: str) -> list[ComparisonResult]:
    results = []
    for model in MODELS:
        started = perf_counter()
        try:
            response = client.models.generate_content(model=model, contents=question)
        except errors.APIError as error:
            elapsed = perf_counter() - started
            results.append(
                ComparisonResult(
                    question=question,
                    model=model,
                    response_seconds=elapsed,
                    output_tokens=None,
                    error=api_error_message(error.code, error.message),
                )
            )
            continue

        elapsed = perf_counter() - started
        usage = response.usage_metadata
        results.append(
            ComparisonResult(
                question=question,
                model=model,
                response_seconds=elapsed,
                output_tokens=usage.candidates_token_count if usage else None,
                answer=response.text,
            )
        )
    return results


def format_results(results: list[ComparisonResult]) -> str:
    lines = [
        "| 質問 | モデル | 応答時間 (秒) | 出力トークン数 | 結果 |",
        "|---|---|---:|---:|---|",
    ]
    for result in results:
        question = " ".join(result.question.split()).replace("|", "\\|")
        tokens = str(result.output_tokens) if result.output_tokens is not None else "不明"
        status = result.error or "成功"
        lines.append(
            f"| {question} | {result.model} | {result.response_seconds:.2f} "
            f"| {tokens} | {status} |"
        )
    return "\n".join(lines)


def main() -> None:
    print("質問を入力してください。空行で終了し、比較表を表示します。")
    client = genai.Client(api_key=get_api_key())
    results = []

    try:
        while True:
            question = input("質問> ").strip()
            if not question:
                break

            for model in MODELS:
                print(f"[{model}] 実行中...")
            question_results = compare_question(client, question)
            results.extend(question_results)
            for result in question_results:
                print(f"\n--- {result.model} の回答 ---")
                if result.error:
                    print(result.error)
                else:
                    print(result.answer or "(回答が空でした)")

        if results:
            print("\n" + format_results(results))
    except EOFError:
        if results:
            print("\n" + format_results(results))
    except KeyboardInterrupt:
        print("\n比較を中断しました。")
        if results:
            print(format_results(results))


if __name__ == "__main__":
    main()