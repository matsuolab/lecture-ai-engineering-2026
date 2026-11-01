"""第1回 宿題（発展）: 応答時間とトークン数を計測し、複数のモデルや質問で比較するスクリプト。

使い方:
    uv run python -m app.benchmark            # 既定のモデル2つ × 既定の質問2つ × 3回
    uv run python -m app.benchmark \
        --models gemini-3.5-flash-lite gemini-3.5-flash \
        --questions "LoRAとは何ですか？" "AIE2026の第2回では何を学びますか？" \
        --repeat 3 --interval 5 --csv results.csv

1回ごとの計測結果と、(モデル, 質問) ごとの集計を表示する。
無料枠のレート制限（429）に当たった呼び出しはエラーとして記録し、計測を続ける。
--interval で呼び出しの間隔を空けると、レート制限に当たりにくくなる。
"""

import argparse
import csv
import statistics
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

from google import genai
from google.genai import errors, types

from app.ask import DEFAULT_QUESTION
from app.config import api_error_message, get_api_key

DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
DEFAULT_QUESTIONS = ["LoRAとは何ですか？", DEFAULT_QUESTION]


@dataclass
class Measurement:
    """1回の呼び出しの計測結果。"""

    model: str
    question: str
    run: int
    latency_s: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    thoughts_tokens: int | None = None  # 思考（thinking）に使ったトークン。出力とは別に数えられる
    total_tokens: int | None = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error

    @property
    def output_tokens_per_s(self) -> float | None:
        if not self.ok or not self.output_tokens or self.latency_s <= 0:
            return None
        return self.output_tokens / self.latency_s


def measure(
    client,
    model: str,
    question: str,
    run: int = 1,
    temperature: float | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> Measurement:
    """1回呼び出して、応答時間（秒）とトークン数を計測する。APIエラーも結果として返す。"""
    config = types.GenerateContentConfig(temperature=temperature) if temperature is not None else None
    start = clock()
    try:
        response = client.models.generate_content(model=model, contents=question, config=config)
    except errors.APIError as e:
        return Measurement(model, question, run, clock() - start, error=f"{e.code}: {api_error_message(e.code, e.message)}")
    latency = clock() - start

    usage = response.usage_metadata
    return Measurement(
        model,
        question,
        run,
        latency,
        input_tokens=usage.prompt_token_count if usage else None,
        output_tokens=usage.candidates_token_count if usage else None,
        thoughts_tokens=usage.thoughts_token_count if usage else None,
        total_tokens=usage.total_token_count if usage else None,
    )


def _mean(values) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def summarize(results: list[Measurement]) -> list[dict]:
    """(モデル, 質問) ごとに、成功した呼び出しの平均・最小・最大などをまとめる。"""
    groups: dict[tuple[str, str], list[Measurement]] = {}
    for r in results:
        groups.setdefault((r.model, r.question), []).append(r)

    rows = []
    for (model, question), items in groups.items():
        ok = [r for r in items if r.ok]
        latencies = [r.latency_s for r in ok]
        rows.append(
            {
                "model": model,
                "question": question,
                "ok": len(ok),
                "errors": len(items) - len(ok),
                "latency_mean": _mean(latencies),
                "latency_min": min(latencies) if latencies else None,
                "latency_max": max(latencies) if latencies else None,
                "input_mean": _mean(r.input_tokens for r in ok),
                "output_mean": _mean(r.output_tokens for r in ok),
                "thoughts_mean": _mean(r.thoughts_tokens for r in ok),
                "tokens_per_s": _mean(r.output_tokens_per_s for r in ok),
            }
        )
    return rows


def _fmt(value, digits: int = 1) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _short(text: str, width: int = 24) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def format_summary(rows: list[dict]) -> str:
    header = ["モデル", "質問", "成功", "失敗", "平均秒", "最小秒", "最大秒", "入力tok", "出力tok", "思考tok", "出力tok/秒"]
    lines = [" | ".join(header), " | ".join("---" for _ in header)]
    for row in rows:
        cells = [
            row["model"],
            _short(row["question"]),
            row["ok"],
            row["errors"],
            _fmt(row["latency_mean"], 2),
            _fmt(row["latency_min"], 2),
            _fmt(row["latency_max"], 2),
            _fmt(row["input_mean"]),
            _fmt(row["output_mean"]),
            _fmt(row["thoughts_mean"]),
            _fmt(row["tokens_per_s"]),
        ]
        lines.append(" | ".join(_fmt(c) for c in cells))
    return "\n".join(lines)


def write_csv(path: str, results: list[Measurement]) -> None:
    fields = list(asdict(results[0]).keys()) + ["output_tokens_per_s"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({**asdict(r), "output_tokens_per_s": r.output_tokens_per_s})


def run_benchmark(
    client,
    models: list[str],
    questions: list[str],
    repeat: int,
    interval: float = 0.0,
    temperature: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Measurement]:
    """モデル × 質問 × 回数 のすべての組み合わせを順に計測する。"""
    results = []
    total = len(models) * len(questions) * repeat
    for model in models:
        for question in questions:
            for run in range(1, repeat + 1):
                if results and interval > 0:
                    sleep(interval)
                r = measure(client, model, question, run, temperature)
                results.append(r)
                status = r.error or (
                    f"{r.latency_s:.2f}s in={_fmt(r.input_tokens)} out={_fmt(r.output_tokens)} "
                    f"thoughts={_fmt(r.thoughts_tokens)}"
                )
                print(f"[{len(results)}/{total}] {model} | {_short(question)} | #{run} {status}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="応答時間とトークン数をモデル・質問ごとに比較する")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help=f"比較するモデル（既定: {' '.join(DEFAULT_MODELS)}）")
    parser.add_argument("--questions", nargs="+", default=DEFAULT_QUESTIONS, help="比較する質問")
    parser.add_argument("--repeat", type=int, default=3, help="組み合わせごとの実行回数（既定: 3）")
    parser.add_argument("--interval", type=float, default=0.0, help="呼び出し間の待ち時間（秒）。レート制限対策")
    parser.add_argument("--temperature", type=float, default=None, help="temperature（省略時はモデルの既定値）")
    parser.add_argument("--csv", help="1回ごとの計測結果を書き出すCSVファイル")
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    started = time.perf_counter()
    results = run_benchmark(client, args.models, args.questions, args.repeat, args.interval, args.temperature)
    elapsed = time.perf_counter() - started

    print("\n## 集計（成功した呼び出しのみ）\n")
    print(format_summary(summarize(results)))

    rate_limited = sum(1 for r in results if r.error.startswith("429"))
    per_minute = len(results) / elapsed * 60 if elapsed > 0 else 0
    print(f"\n[全体] {len(results)} 回 / {elapsed:.1f} 秒（約 {per_minute:.1f} 回/分）, レート制限（429）: {rate_limited} 回")

    if args.csv:
        write_csv(args.csv, results)
        print(f"[csv] {args.csv} に書き出しました")


if __name__ == "__main__":
    main()
