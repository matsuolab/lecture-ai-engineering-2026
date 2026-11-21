"""第5回宿題: 検索件数(AIE_TOP_K) × 前後ページ(AIE_NEIGHBORS) を、同じ質問で実測する。

使い方（リポジトリ直下で）:
    uv run python lectures/05/run_matrix.py              # 5問 × 6条件 × 3回 = 90回
    uv run python lectures/05/run_matrix.py --repeats 1  # まず動作確認（30回）

質問・モデル・資料は固定。条件の順番は、質問ごとに1回ずつ巡回する（キャッシュ等の偏りを避ける）。
失敗した条件だけを自動で再実行する（成功済みは再利用）。途中で止まっても同じコマンドで再開できる。
出力: lectures/05/matrix_results.jsonl（全記録）と matrix_summary.md（条件別の集計）。
「正しい回答か」は自動では判定しない。jsonl の answer を人が読んで確かめる。
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

# (名前, 質問, 答えに必要なページ番号[回をまたがない]。空なら「資料にない」質問)
# 必要ページは「答えが書いてあるページ」だけ。質問の主題のページ(A)は含めない。
QUESTIONS = [
    ("QLoRA", "QLoRAで学習した演習のモデルは、JSONなど形式は直る一方で、何は直らないとされていますか？", [53]),
    ("HITL", "人が毎回承認する human-in-the-loop の形にしても、送金や注文のようなツールで起きうる問題は何ですか？", [26, 27]),
    ("事後学習", "事後学習で答え方を直せるのに対して、使うときに考えさせると難問の正答率はどう変わりますか？", [25]),
    ("複数ページ", "コンパクションとセッションをまたぐメモリの違いは？ 日々のメモは全部長期メモリになる？", [13, 39, 40]),
    ("資料にない", "今回作ったRAGの実測平均応答時間と正答率は？", []),
]

# (検索件数, 前後ページ)
CONFIGS = [(2, 0), (2, 1), (3, 0), (3, 1), (5, 0), (5, 1)]


def cited_pages(answer: str) -> set[int]:
    """回答中の「p.51, 52」「PDF p.39、p.65」のようなページ番号を拾う。"""
    pages = set()
    for m in re.finditer(r"p\.?\s*(\d+(?:\s*[,、/・]\s*(?:p\.?\s*)?\d+)*)", answer):
        pages.update(int(n) for n in re.findall(r"\d+", m.group(1)))
    return pages


def retrieved_pages(text: str) -> set[int]:
    pages = set()
    for line in re.findall(r"^\[retrieved\] (.+)$", text, flags=re.M):
        pages.update(int(n) for n in re.findall(r"-p(\d+)", line))
    return pages


def run_once(question: str, top_k: int, neighbors: int) -> dict:
    env = {**os.environ, "AIE_TOP_K": str(top_k), "AIE_NEIGHBORS": str(neighbors)}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "app.agent", "--trace", question],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=240,
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    out, err = proc.stdout, proc.stderr
    if proc.returncode != 0:
        # エラー文は標準出力に出る。標準エラーは [retrieved] 行なので、両方を見せる。
        return {"error": f"exit {proc.returncode}: {out.strip()[-200:]} | {err.strip()[-100:]}"}
    answer = out.split("--- trace ---")[0].strip()
    trace = out
    t = re.search(r"回答完了まで ([\d.]+) 秒", trace)
    u = re.search(r"入力 ([\d,]+) tokens / 出力 ([\d,]+) tokens / モデル応答 (\d+) 回", trace)
    c = re.search(r"\$([\d.]+) USD", trace)
    if not (t and u and c):
        return {"error": "trace解析失敗", "answer": answer[:300]}
    return {
        "answer": answer,
        "time": float(t.group(1)),
        "in_tokens": int(u.group(1).replace(",", "")),
        "out_tokens": int(u.group(2).replace(",", "")),
        "responses": int(u.group(3)),
        "cost": float(c.group(1)),
        "search_calls": len(re.findall(r"\[tool call\]\s+search_materials", trace)),
        "tool_calls": len(re.findall(r"\[tool call\]", trace)),
        "retrieved": sorted(retrieved_pages(err + out)),
        "cited": sorted(cited_pages(answer)),
    }


def retryable(error: str) -> bool:
    return any(w in error for w in ("レート制限", "429", "503", "混み合って", "timeout"))


def run_with_retry(question: str, top_k: int, neighbors: int, attempts: int = 3) -> dict:
    for i in range(attempts):
        r = run_once(question, top_k, neighbors)
        if "error" not in r or not retryable(r["error"]) or i == attempts - 1:
            return r
        wait = 15 * (i + 1)
        print(f"    待って再試行します（{wait}秒）: {r['error'][:60]}", flush=True)
        time.sleep(wait)
    return r


def summarize(records: list[dict]) -> str:
    lines = ["# 第5回宿題 検索件数 × 前後ページ の実測まとめ\n",
             "retrieved=必要ページが検索で取れた割合 / cited=回答が必要ページをすべて引用した割合。"
             "正しさは未判定（jsonl の answer を読んで確かめる）。\n"]
    for name, _, need in QUESTIONS:
        lines.append(f"\n## {name}（必要ページ: {need or 'なし＝資料にない質問'}）\n")
        lines.append("| k | 前後 | 回数 | retrieved | cited | 検索回数 | 入力tok | 出力tok | 時間(秒) | 費用(USD) |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for k, n in CONFIGS:
            rs = [r for r in records if r["q"] == name and r["k"] == k and r["n"] == n and "error" not in r]
            errs = sum(1 for r in records if r["q"] == name and r["k"] == k and r["n"] == n and "error" in r)
            if not rs:
                lines.append(f"| {k} | {n} | 0（エラー{errs}） | - | - | - | - | - | - | - |")
                continue
            if need:
                ret = sum(all(p in r["retrieved"] for p in need) for r in rs)
                cit = sum(all(p in r["cited"] for p in need) for r in rs)
                ret_s, cit_s = f"{ret}/{len(rs)}", f"{cit}/{len(rs)}"
            else:
                ret_s = cit_s = "-"
            avg = lambda key: statistics.mean(r[key] for r in rs)
            lines.append(
                f"| {k} | {n} | {len(rs)}{f'（エラー{errs}）' if errs else ''} | {ret_s} | {cit_s} | "
                f"{avg('search_calls'):.1f} | {avg('in_tokens'):,.0f} | {avg('out_tokens'):,.0f} | "
                f"{avg('time'):.1f} | {avg('cost'):.4f} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=3, help="各実行のあとに待つ秒数（レート制限対策）")
    parser.add_argument("--questions", default="", help="実行する質問名をカンマ区切りで（例: QLoRA,HITL）。省略で全部")
    parser.add_argument("--ks", default="", help="実行する検索件数をカンマ区切りで（例: 2,3）。省略で全部")
    args = parser.parse_args()

    only_q = {q for q in args.questions.split(",") if q}
    only_k = {int(k) for k in args.ks.split(",") if k}
    jsonl = OUT_DIR / "matrix_results.jsonl"

    # 前回までに成功した記録は残す。範囲内で失敗・未実行の条件だけ実行する（途中再開もできる）
    results = {}
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if "error" not in r:
                    results[(r["rep"], r["q"], r["k"], r["n"])] = r

    todo = [(rep, name, question, k, n)
            for rep in range(1, args.repeats + 1)
            for name, question, _ in QUESTIONS if not only_q or name in only_q
            for k, n in CONFIGS if not only_k or k in only_k]
    pending = [t for t in todo if (t[0], t[1], t[3], t[4]) not in results]
    print(f"範囲内 {len(todo)} 条件のうち、実行するのは {len(pending)} 回（残りは前回の記録を再利用）", flush=True)

    def save() -> None:
        with jsonl.open("w", encoding="utf-8") as f:
            for rec in results.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    failed = 0
    for i, (rep, name, question, k, n) in enumerate(pending, 1):
        r = run_with_retry(question, k, n)
        rec = {"rep": rep, "q": name, "k": k, "n": n, **r}
        if "error" in rec:
            failed += 1
            status = rec["error"]
        else:
            results[(rep, name, k, n)] = rec
            save()
            status = f"{r['time']}s ${r['cost']:.4f} retrieved={r['retrieved']}"
        print(f"[{i}/{len(pending)}] rep{rep} {name} k={k} n={n}: {status}", flush=True)
        time.sleep(args.sleep)

    save()
    (OUT_DIR / "matrix_summary.md").write_text(summarize(list(results.values())), encoding="utf-8")
    print(f"\n保存: {jsonl.name}, matrix_summary.md（失敗{failed}件。残っていれば同じコマンドをもう一度）")


if __name__ == "__main__":
    main()
