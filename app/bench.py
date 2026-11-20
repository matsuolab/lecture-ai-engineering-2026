"""第1回 宿題（発展）：応答時間とトークン数を計測し、モデルや質問ごとに比べる。

使い方（リポジトリのルートで実行）:
    uv run python -m app.bench
        既定の 2 モデル × 3 問 × 3 回 = 18 回を、13 秒間隔で順に実行する（約 5 分）
    uv run python -m app.bench --models gemini-3.5-flash-lite --repeat 1 --interval 5 --label test
        モデル・回数・間隔を変える（まずはこれで動作確認）
    uv run python -m app.bench --models gemini-3.5-flash-lite \
        --questions "LoRAを一言で説明してください。" --repeat 20 --interval 0 --label burst
        間隔をあけずに連続で送り、レート制限（429）に当たる様子を観察する

結果は 1 回の呼び出しごとに lectures/01/bench_results.csv に追記され、
最後にモデル × 質問ごとの集計を Markdown の表で表示する（answer.md にそのまま貼れる）。
API キーは CSV にも画面にも出さない。
"""

import argparse
import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import api_error_message, get_api_key

DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

# 答えの長さが変わるように選んだ質問（短い／ふつう／長い）
DEFAULT_QUESTIONS = [
    "LoRAを一言で説明してください。",
    "LoRAとは何ですか？",
    "LoRAとQLoRAの違いを、仕組み・メモリ使用量・精度の観点から詳しく説明してください。",
]

# gemini-3.8-flash の無料枠は毎分 5 リクエスト → 12 秒に 1 回より遅く送る
DEFAULT_INTERVAL = 13.0

OUT_PATH = Path("lectures/01/bench_results.csv")
FIELDS = [
    "time", "label", "model", "question_id", "question", "repeat",
    "status", "seconds", "input_tokens", "output_tokens", "thinking_tokens",
    "total_tokens", "answer_chars", "error",
]


def measure(client: genai.Client, model: str, question: str) -> dict:
    """1 回だけ呼び出し、応答時間とトークン数を返す。API エラーも結果として残す。"""
    start = time.perf_counter()
    try:
        response = client.models.generate_content(model=model, contents=question)
    except errors.APIError as e:
        return {
            "status": e.code,
            "seconds": round(time.perf_counter() - start, 3),
            "error": api_error_message(e.code, e.message or "")[:200],
        }
    seconds = time.perf_counter() - start

    usage = response.usage_metadata
    return {
        "status": 200,
        "seconds": round(seconds, 3),
        "input_tokens": getattr(usage, "prompt_token_count", None),
        "output_tokens": getattr(usage, "candidates_token_count", None),
        # 思考（thinking）するモデルでは、答えとは別に思考のトークンが数えられる
        "thinking_tokens": getattr(usage, "thoughts_token_count", None),
        "total_tokens": getattr(usage, "total_token_count", None),
        "answer_chars": len(response.text or ""),
    }


def append_row(row: dict) -> None:
    """1 行ずつ CSV に追記する（途中で止めても、そこまでの結果は残る）。"""
    is_new = not OUT_PATH.exists()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def _fmt(value, digits: int = 1) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def print_summary(rows: list[dict]) -> None:
    """モデル × 質問ごとに平均をとり、Markdown の表で表示する。"""
    if not rows:
        return
    print("\n## 集計（時間は秒。平均は成功した呼び出しのみ）\n")
    print("| モデル | 質問 | 成功/全体 | 平均時間 | 最小〜最大 | 入力 | 出力 | 思考 | (出力+思考)/秒 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for model, qid in dict.fromkeys((r["model"], r["question_id"]) for r in rows):
        group = [r for r in rows if r["model"] == model and r["question_id"] == qid]
        ok = [r for r in group if r["status"] == 200]
        secs = [r["seconds"] for r in ok]
        # 思考のトークンも生成に時間がかかるので、出力と合わせて 1 秒あたりの量を出す
        speeds = [
            ((r["output_tokens"] or 0) + (r["thinking_tokens"] or 0)) / r["seconds"]
            for r in ok
            if r["seconds"] > 0
        ]
        span = f"{min(secs):.2f}〜{max(secs):.2f}" if secs else "-"
        print(
            f"| {model} | Q{qid} | {len(ok)}/{len(group)} | {_fmt(_mean(secs), 2)} | {span} | "
            f"{_fmt(_mean([r['input_tokens'] for r in ok]), 0)} | "
            f"{_fmt(_mean([r['output_tokens'] for r in ok]), 0)} | "
            f"{_fmt(_mean([r['thinking_tokens'] for r in ok]), 0)} | "
            f"{_fmt(_mean(speeds), 1)} |"
        )

    failed = [r for r in rows if r["status"] != 200]
    if failed:
        print("\n## エラー\n")
        for r in failed:
            print(f"- {r['time']} {r['model']} Q{r['question_id']} 回{r['repeat']}: {r['status']} {r['error']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="応答時間とトークン数を計測する")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--questions", nargs="+", default=DEFAULT_QUESTIONS)
    parser.add_argument("--repeat", type=int, default=3, help="同じ質問を何回ずつ送るか")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL, help="呼び出しの間隔（秒）")
    parser.add_argument("--label", default="base", help="CSV に残す実験名（例：base, burst）")
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())  # クライアントは 1 回だけ作る（計測時間に含めない）
    total = args.repeat * len(args.questions) * len(args.models)
    print(f"[計測] {len(args.models)} モデル × {len(args.questions)} 問 × {args.repeat} 回 = {total} 回、間隔 {args.interval} 秒")
    for qid, question in enumerate(args.questions, 1):
        print(f"  Q{qid}: {question}")
    print(f"  結果の保存先: {OUT_PATH}\n")

    rows: list[dict] = []
    n = 0
    try:
        # 回 → 質問 → モデルの順に回し、時間帯による差が特定のモデルに偏らないようにする
        for rep in range(1, args.repeat + 1):
            for qid, question in enumerate(args.questions, 1):
                for model in args.models:
                    n += 1
                    if n > 1 and args.interval > 0:
                        time.sleep(args.interval)
                    result = measure(client, model, question)
                    row = {
                        "time": datetime.now().isoformat(timespec="seconds"),
                        "label": args.label,
                        "model": model,
                        "question_id": qid,
                        "question": question,
                        "repeat": rep,
                        **result,
                    }
                    rows.append(row)
                    append_row(row)
                    if result["status"] == 200:
                        thinking = result["thinking_tokens"]
                        print(
                            f"[{n}/{total}] {model} Q{qid} 回{rep}: {result['seconds']:.2f} 秒 | "
                            f"入力 {result['input_tokens']} / 出力 {result['output_tokens']} / "
                            f"思考 {'-' if thinking is None else thinking}"
                        )
                    else:
                        print(f"[{n}/{total}] {model} Q{qid} 回{rep}: エラー {result['status']}（{result['error']}）")
    except KeyboardInterrupt:
        print("\n[中断] ここまでの結果を集計します")

    print_summary(rows)


if __name__ == "__main__":
    main()
