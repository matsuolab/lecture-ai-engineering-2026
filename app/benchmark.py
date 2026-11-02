"""第1回 宿題（発展）: 応答時間とトークン数を、モデルと質問ごとに計測する。

使い方:
    uv run python -m app.benchmark
    uv run python -m app.benchmark --models gemini-3.5-flash-lite gemini-3.5-flash --repeat 3 --sleep 5

1回の呼び出しごとに1行を CSV に追記し、最後にモデル×質問ごとの集計を表示する。
エラー（429・503 など）も再試行せず、そのまま1行として記録する（レート制限の考察に使う）。
"""

import argparse
import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import errors

from app.ask import DEFAULT_QUESTION
from app.config import get_api_key

DEFAULT_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

# 出力の長さが違う3種類の質問
QUESTIONS = {
    "short": "日本の首都はどこですか？一言で答えてください。",
    "general": "LoRAとは何ですか？",
    "course": DEFAULT_QUESTION,
}

FIELDS = [
    "timestamp", "model", "question", "run", "status", "latency_s",
    "prompt_tokens", "output_tokens", "thoughts_tokens", "total_tokens", "output_chars",
]


def measure(client: genai.Client, model: str, question: str) -> dict:
    """1回呼び出し、応答時間とトークン数を返す。エラーも記録用の dict にして返す。"""
    start = time.perf_counter()
    try:
        response = client.models.generate_content(model=model, contents=question)
    except errors.APIError as e:
        return {"status": e.code, "latency_s": round(time.perf_counter() - start, 2)}
    latency = time.perf_counter() - start

    usage = response.usage_metadata
    if usage is None:
        return {"status": "ok", "latency_s": round(latency, 2), "output_chars": len(response.text or "")}
    return {
        "status": "ok",
        "latency_s": round(latency, 2),
        "prompt_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
        # 思考（thinking）に使ったトークン。出力トークンとは別に数えられる
        "thoughts_tokens": getattr(usage, "thoughts_token_count", None),
        "total_tokens": usage.total_token_count,
        "output_chars": len(response.text or ""),
    }


def median_of(rows: list[dict], field: str):
    values = [r[field] for r in rows if r.get(field) is not None]
    return round(statistics.median(values), 2) if values else "-"


def summarize(rows: list[dict]) -> None:
    """モデル×質問ごとに、成功回数と各値の中央値を表示する。"""
    print("\n[集計] model / question / 成功/全体 / 応答時間(s) / 出力 / 思考（いずれも中央値）")
    for model, qid in sorted({(r["model"], r["question"]) for r in rows}):
        group = [r for r in rows if r["model"] == model and r["question"] == qid]
        ok = [r for r in group if r["status"] == "ok"]
        print(
            f"{model:<24} {qid:<8} {len(ok)}/{len(group)}  "
            f"{median_of(ok, 'latency_s')}  {median_of(ok, 'output_tokens')}  {median_of(ok, 'thoughts_tokens')}"
        )
    errors_seen = [r for r in rows if r["status"] != "ok"]
    if errors_seen:
        print("\n[エラー] " + ", ".join(f"{r['model']}:{r['status']}" for r in errors_seen))


def main() -> None:
    parser = argparse.ArgumentParser(description="応答時間とトークン数を計測する")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--questions", nargs="+", default=list(QUESTIONS), choices=list(QUESTIONS))
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=5.0, help="呼び出しの間の待ち時間（秒）")
    parser.add_argument("--out", type=Path, default=Path("lectures/01/benchmark.csv"))
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    new_file = not args.out.exists()
    rows = []
    with args.out.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        # モデルを内側のループにして、同じモデルへの呼び出しが連続しないようにする
        for run in range(1, args.repeat + 1):
            for qid in args.questions:
                for model in args.models:
                    row = {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "model": model, "question": qid, "run": run,
                    }
                    row |= measure(client, model, QUESTIONS[qid])
                    writer.writerow(row)
                    f.flush()  # 途中で止めても、そこまでの結果は残す
                    rows.append(row)
                    print(
                        f"run{run} {qid:<8} {model:<24} {row['status']} {row['latency_s']}s "
                        f"out={row.get('output_tokens')} think={row.get('thoughts_tokens')}"
                    )
                    time.sleep(args.sleep)
    summarize(rows)


if __name__ == "__main__":
    main()
