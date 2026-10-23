"""第1回 宿題(発展): モデル×質問で応答時間とトークン数を計測し、集計する。

使い方(リポジトリのルートで。GEMINI_API_KEY は環境変数で渡す):
    PYTHONPATH=. uv run python lectures/01/src/measure_llm.py run --repeats 3 --out lectures/01/results/measurements.jsonl
    PYTHONPATH=. uv run python lectures/01/src/measure_llm.py summary lectures/01/results/measurements.jsonl lectures/01/results/measurements_long.jsonl
テスト: uv run pytest lectures/01/src

run は 1 回の呼び出しごとに JSONL を追記する(途中で止まっても記録は残る)。
モデルごとの RPM を超えないよう、同じモデルへの呼び出し間隔を空ける。
summary は 1 つ以上の JSONL からモデル別・質問別の Markdown 表を標準出力に出す。
"""

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import api_error_message, get_api_key

# 比較するモデルと無料枠の RPM(AI Studio のレート制限画面の値)
MODEL_RPM = {
    "gemini-3.5-flash-lite": 15,
    "gemini-3.1-flash-lite": 15,
    "gemini-3.8-flash": 5,
    "gemma-4-31b-it": 30,
}
RPM_MARGIN_SECONDS = 1.0

QUESTIONS = {
    # 短い事実質問
    "short": "LoRAとは何ですか？",
    # 前提が偽の質問(実在するのはカモシカに関するジンクス)。知らないことを作り話で答えるかを見る
    "false_premise": "秋田大学の学生に伝わっている、ヒグマに関するジンクスはなんですか？",
    # 長い出力を要する質問
    "long": (
        "LoRAの仕組みについて解説する記事を、全体像から、低ランク分解の考え方など技術的側面を踏まえ、"
        "この手法のメリットやデメリット、実際の活用例について整理し、詳しく説明してください。"
        "聴衆は専門外の大学1年生が理解できる程度の言葉で読みやすい記事を心がけてください。"
    ),
}

STATUS_OK = "ok"


def build_record(model, question_id, repeat, latency_s, chunks=None, usage=None, text=None, error=None) -> dict:
    """1 回の呼び出し結果を JSONL の 1 行分にする。error があれば失敗として記録する。

    chunks は回答テキストを含むチャンクごとの [受信時刻(s), 文字数, 累積出力トークン数 or None]。
    API が返す最小単位はチャンク(数トークン〜数十トークン)で、トークン単位の時刻は取れない。
    latency_s は送信から最後のチャンクまで、ttft_s は送信から最初の回答テキストまで。
    思考(thinking)は回答テキストより前に行われるので、ttft_s に含まれる。
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model,
        "question_id": question_id,
        "repeat": repeat,
        "latency_s": round(latency_s, 3),
    }
    if error is not None:
        return {**record, "status": error.code, "error": (error.message or "")[:200]}

    ttft_s = chunks[0][0] if chunks else latency_s
    return {
        **record,
        "status": STATUS_OK,
        "ttft_s": ttft_s,
        "output_s": round(latency_s - ttft_s, 3),
        "n_chunks": len(chunks or []),
        "chunks": chunks,
        "prompt_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
        "thinking_tokens": usage.thoughts_token_count or 0,
        "total_tokens": usage.total_token_count,
        "text": text,
    }


def run(models, question_ids, repeats, out_path: Path) -> None:
    client = genai.Client(api_key=get_api_key())
    last_call = {}  # モデル -> 直近の呼び出し開始時刻
    with out_path.open("a", encoding="utf-8") as out:
        # 時間帯の偏りを避けるため、モデルを一番内側にして交互に回す
        for repeat in range(1, repeats + 1):
            for qid in question_ids:
                for model in models:
                    wait = last_call.get(model, 0) + 60 / MODEL_RPM[model] + RPM_MARGIN_SECONDS - time.monotonic()
                    if wait > 0:
                        time.sleep(wait)
                    last_call[model] = time.monotonic()
                    record = call_once(client, model, qid, repeat)
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    out.flush()
                    print(f"{model} {qid} #{repeat}: {record['status']} {record['latency_s']}s", file=sys.stderr)


def call_once(client, model, question_id, repeat) -> dict:
    start = time.perf_counter()
    chunks = []
    usage = None
    texts = []
    try:
        for chunk in client.models.generate_content_stream(model=model, contents=QUESTIONS[question_id]):
            received_s = time.perf_counter() - start
            # usage_metadata は累積値で、最後のチャンクのものが合計になる
            if chunk.usage_metadata:
                usage = chunk.usage_metadata
            if not chunk.text:
                continue
            texts.append(chunk.text)
            cumulative_tokens = chunk.usage_metadata.candidates_token_count if chunk.usage_metadata else None
            chunks.append([round(received_s, 3), len(chunk.text), cumulative_tokens])
    except errors.APIError as e:
        print(api_error_message(e.code, e.message), file=sys.stderr)
        return build_record(model, question_id, repeat, time.perf_counter() - start, error=e)
    latency_s = time.perf_counter() - start
    return build_record(model, question_id, repeat, latency_s, chunks=chunks, usage=usage, text="".join(texts))


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize(records: list[dict], keys: tuple[str, ...]) -> list[dict]:
    """keys(例: ("model",))ごとに、成功した呼び出しの平均などを集計する。"""
    groups = defaultdict(list)
    for r in records:
        groups[tuple(r[k] for k in keys)].append(r)

    rows = []
    for group_key, group in sorted(groups.items()):
        ok = [r for r in group if r["status"] == STATUS_OK]
        row = dict(zip(keys, group_key))
        row.update(n_ok=len(ok), n_error=len(group) - len(ok))
        if ok:
            latencies = [r["latency_s"] for r in ok]
            # 出力速度は最初の回答テキスト以降の区間で測る(思考は TTFT 側に入る)
            streamed = [r for r in ok if r["output_s"] > 0]
            row.update(
                latency_median=statistics.median(latencies),
                latency_min=min(latencies),
                latency_max=max(latencies),
                ttft_median=statistics.median(r["ttft_s"] for r in ok),
                output_s_median=statistics.median(r["output_s"] for r in ok),
                prompt_tokens=statistics.mean(r["prompt_tokens"] for r in ok),
                output_tokens=statistics.mean(r["output_tokens"] for r in ok),
                thinking_tokens=statistics.mean(r["thinking_tokens"] for r in ok),
            )
            if streamed:
                row["tokens_per_s"] = statistics.mean(r["output_tokens"] / r["output_s"] for r in streamed)
        rows.append(row)
    return rows


def format_table(rows: list[dict], keys: tuple[str, ...]) -> str:
    columns = [
        *keys, "n_ok", "n_error", "latency_median", "latency_min", "latency_max",
        "ttft_median", "output_s_median", "prompt_tokens", "output_tokens", "thinking_tokens", "tokens_per_s",
    ]
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in rows:
        cells = [f"{row[c]:.1f}" if isinstance(row.get(c), float) else str(row.get(c, "-")) for c in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="応答時間とトークン数を計測する")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="計測して JSONL に追記する")
    run_parser.add_argument("--models", nargs="+", default=list(MODEL_RPM), choices=list(MODEL_RPM))
    run_parser.add_argument("--questions", nargs="+", default=list(QUESTIONS), choices=list(QUESTIONS))
    run_parser.add_argument("--repeats", type=int, default=3)
    run_parser.add_argument("--out", type=Path, required=True)

    summary_parser = sub.add_parser("summary", help="JSONL を Markdown の表にする")
    summary_parser.add_argument("paths", type=Path, nargs="+")

    args = parser.parse_args()
    if args.command == "run":
        run(args.models, args.questions, args.repeats, args.out)
        return

    records = [r for path in args.paths for r in load_records(path)]
    for keys in [("model",), ("model", "question_id")]:
        print(format_table(summarize(records, keys), keys), end="\n\n")


if __name__ == "__main__":
    main()
