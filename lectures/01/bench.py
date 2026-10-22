"""複数モデル・質問の応答時間とトークン数を計測する。"""

import csv
import statistics
import time
from pathlib import Path
from typing import Callable

from google import genai

from app.ask import DEFAULT_QUESTION, get_api_key

MODELS = (("gemini-3.5-flash-lite", 3), ("gemini-3.8-flash", 1))
QUESTIONS = (
    "LoRAとは何ですか？",
    "生成AIを初めて学ぶ人に向けて、仕組み、活用例、注意点を含めて詳しく説明してください。",
    DEFAULT_QUESTION,
)
FIELDNAMES = (
    "model",
    "question",
    "run",
    "seconds",
    "input_tokens",
    "output_tokens",
    "status",
)


def run_trial(
    client,
    model: str,
    question: str,
    run: int,
    perf_counter: Callable[[], float] = time.perf_counter,
) -> dict:
    started = perf_counter()
    try:
        response = client.models.generate_content(model=model, contents=question)
    except Exception as error:
        return {
            "model": model,
            "question": question,
            "run": run,
            "seconds": perf_counter() - started,
            "input_tokens": "",
            "output_tokens": "",
            "status": f"error: {type(error).__name__}",
        }

    usage = response.usage_metadata
    input_tokens = None if usage is None else usage.prompt_token_count
    output_tokens = None if usage is None else usage.candidates_token_count
    return {
        "model": model,
        "question": question,
        "run": run,
        "seconds": perf_counter() - started,
        "input_tokens": "" if input_tokens is None else input_tokens,
        "output_tokens": "" if output_tokens is None else output_tokens,
        "status": "ok",
    }


def run_benchmark(
    client,
    models=MODELS,
    questions=QUESTIONS,
    interval_seconds: float = 5,
    sleep_fn: Callable[[float], None] = time.sleep,
    perf_counter: Callable[[], float] = time.perf_counter,
) -> list[dict]:
    rows = []
    for model, repetitions in models:
        for question in questions:
            for run in range(1, repetitions + 1):
                if rows:
                    sleep_fn(interval_seconds)
                rows.append(run_trial(client, model, question, run, perf_counter))
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict]) -> dict[str, dict]:
    summaries = {}
    for row in rows:
        summary = summaries.setdefault(
            row["model"], {"seconds": [], "output_tokens": [], "failures": 0}
        )
        if row["status"].startswith("error:"):
            summary["failures"] += 1
            continue
        summary["seconds"].append(row["seconds"])
        if row["output_tokens"] != "":
            summary["output_tokens"].append(row["output_tokens"])

    return {
        model: {
            "average_seconds": statistics.mean(values["seconds"])
            if values["seconds"]
            else None,
            "average_output_tokens": statistics.mean(values["output_tokens"])
            if values["output_tokens"]
            else None,
            "failures": values["failures"],
        }
        for model, values in summaries.items()
    }


def print_summary(rows: list[dict]) -> None:
    for model, summary in summarize(rows).items():
        average_seconds = summary["average_seconds"]
        average_tokens = summary["average_output_tokens"]
        seconds_text = "-" if average_seconds is None else f"{average_seconds:.2f}"
        tokens_text = "-" if average_tokens is None else f"{average_tokens:.1f}"
        print(
            f"{model}: 平均秒数={seconds_text}, "
            f"平均出力トークン数={tokens_text}, 失敗件数={summary['failures']}"
        )


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    rows = run_benchmark(client)
    output_path = Path(__file__).with_name("bench.csv")
    write_csv(rows, output_path)
    print(f"結果を {output_path} に保存しました。")
    print_summary(rows)


if __name__ == "__main__":
    main()