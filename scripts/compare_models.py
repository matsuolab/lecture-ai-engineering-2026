"""複数の Gemini モデルの応答時間とトークン数を比較する。"""

import argparse
import json
import random
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import api_error_message, get_api_key

DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
DEFAULT_QUESTION = "LoRAとは何ですか？"
DEFAULT_INTERVAL_SECONDS = 10
DEFAULT_MAX_RETRIES = 3
LOG_PATH = Path("learning_log/model_comparison.jsonl")


def generate_with_retry(client, model: str, question: str, max_retries: int):
    for attempt in range(max_retries + 1):
        started = time.perf_counter()
        try:
            response = client.models.generate_content(model=model, contents=question)
        except errors.APIError as error:
            if error.code not in (429, 503) or attempt == max_retries:
                raise
            delay = min(10 * (2**attempt), 60) + random.uniform(0, 1)
            print(f"[待機] APIエラー {error.code}。{delay:.1f}秒後に再試行します。")
            time.sleep(delay)
        else:
            return response, time.perf_counter() - started


def run_comparison(
    client,
    models: list[str],
    question: str,
    runs: int,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> list[dict]:
    results = []
    request_count = 0
    for run in range(1, runs + 1):
        offset = (run - 1) % len(models)
        ordered_models = models[offset:] + models[:offset]
        for model in ordered_models:
            if request_count and interval_seconds:
                print(f"[待機] 次のリクエストまで{interval_seconds:g}秒")
                time.sleep(interval_seconds)
            response, elapsed = generate_with_retry(client, model, question, max_retries)
            usage = response.usage_metadata
            results.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "run": run,
                "question": question,
                "elapsed_seconds": elapsed,
                "input_tokens": usage.prompt_token_count if usage is not None else None,
                "output_tokens": usage.candidates_token_count if usage is not None else None,
                "answer": response.text,
            })
            request_count += 1
    return results


def summarize(results: list[dict]) -> dict[str, dict[str, float | None]]:
    summaries = {}
    for model in dict.fromkeys(result["model"] for result in results):
        model_results = [result for result in results if result["model"] == model]
        summaries[model] = {
            metric: statistics.median(values) if values else None
            for metric, values in (
                ("elapsed_seconds", [result["elapsed_seconds"] for result in model_results]),
                ("input_tokens", [result["input_tokens"] for result in model_results if result["input_tokens"] is not None]),
                ("output_tokens", [result["output_tokens"] for result in model_results if result["output_tokens"] is not None]),
            )
        }
    return summaries


def print_comparison(summaries: dict[str, dict[str, float | None]]) -> None:
    print("\n[中央値]")
    for model, metrics in summaries.items():
        print(
            f"{model}: 応答時間 {metrics['elapsed_seconds']:.2f} 秒, "
            f"入力 {metrics['input_tokens'] if metrics['input_tokens'] is not None else '不明'} tokens, "
            f"出力 {metrics['output_tokens'] if metrics['output_tokens'] is not None else '不明'} tokens"
        )

    fastest_model = min(summaries, key=lambda model: summaries[model]["elapsed_seconds"])
    token_models = [model for model in summaries if summaries[model]["output_tokens"] is not None]
    fewest_tokens_model = min(token_models, key=lambda model: summaries[model]["output_tokens"]) if token_models else None

    if len(summaries) > 1:
        times = [metrics["elapsed_seconds"] for metrics in summaries.values()]
        fastest, slowest = min(times), max(times)
        if slowest:
            print(f"応答時間の差: {slowest - fastest:.2f} 秒 ({(slowest - fastest) / slowest * 100:.1f}%)")
        for metric, label in (("input_tokens", "入力トークン数"), ("output_tokens", "出力トークン数")):
            counts = [metrics[metric] for metrics in summaries.values() if metrics[metric] is not None]
            if len(counts) > 1:
                fewest, most = min(counts), max(counts)
                percent = (most - fewest) / most * 100 if most else 0
                print(f"{label}の差: {most - fewest:g} tokens ({percent:.1f}%)")

    if fewest_tokens_model is None:
        print("[判定] 出力トークン数が取得できず、総合比較できません。")
    elif fastest_model == fewest_tokens_model:
        print(f"[判定] {fastest_model} は最速かつ出力トークン数が最少です（測定指標上の優位）。")
    else:
        print(f"[判定] トレードオフです。最速: {fastest_model}、出力トークン最少: {fewest_tokens_model}。")
    print("回答の正確さ・有用さは、下の回答例を読んで別途比較してください。")


def main() -> None:
    parser = argparse.ArgumentParser(description="Geminiモデルの応答時間とトークン数を比較する")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="比較するモデル名（複数指定）")
    parser.add_argument("--runs", type=int, default=3, help="モデルごとの測定回数（既定: 3）")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="各モデルに送る同じ質問")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS, help="リクエスト間隔・秒（既定: 10）")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="429/503時の再試行回数（既定: 3）")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs は1以上を指定してください")
    if len(args.models) < 2:
        parser.error("--models は2つ以上指定してください")
    if args.interval < 0:
        parser.error("--interval は0以上を指定してください")
    if args.max_retries < 0:
        parser.error("--max-retries は0以上を指定してください")

    try:
        client = genai.Client(api_key=get_api_key())
        results = run_comparison(
            client,
            args.models,
            args.question,
            args.runs,
            interval_seconds=args.interval,
            max_retries=args.max_retries,
        )
    except errors.APIError as error:
        print(api_error_message(error.code, error.message))
        raise SystemExit(1)

    summaries = summarize(results)
    print_comparison(summaries)
    print("\n[回答例]")
    for model in args.models:
        first_answer = next(result["answer"] for result in results if result["model"] == model)
        print(f"\n--- {model} ---\n{first_answer}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        for result in results:
            log_file.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(f"\n[ログ] {LOG_PATH}")


if __name__ == "__main__":
    main()