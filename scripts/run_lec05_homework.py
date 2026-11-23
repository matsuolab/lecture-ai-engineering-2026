"""第5回 宿題（基礎・実装）の比較を、同じ質問・同じモデルでまとめて実行する。

    uv run python scripts/run_lec05_homework.py              # 宿題：rag / topk10 / neighbors を比べる
    uv run python scripts/run_lec05_homework.py --exercise   # 演習の表（全文投入・ベクトル・Tree・Graph）も測る

方式（mode）
    rag        通常のベクトル検索（RAG_TOP_K=5）。比較の基準
    topk10     宿題・基礎：config の RAG_TOP_K だけを 10 に変えたもの
    neighbors  宿題・実装：上位5件の各ページに、同じ資料の前後1ページの本文を付けたもの

出力（lectures/05/results/）
    homework_runs.json    各実行の回答・ツール呼び出し・取得ページ・--trace の表示・時間・トークン数・費用
    homework_report.md    上をまとめた比較表（answer.md へ転記する元）
"""

import argparse
import contextlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai.exceptions import ModelHTTPError  # noqa: E402
from pydantic_ai.messages import ToolCallPart, ToolReturnPart  # noqa: E402

from app import agent as agent_module  # noqa: E402
from app import retrieval, tools  # noqa: E402
from app.config import MODEL  # noqa: E402

OUT_DIR = ROOT / "lectures/05/results"

# 根拠ページは、lectures.json の本文を読んで先に決めた（演習スライド20の質問＋前後ページが要る質問）
QUESTIONS = [
    {"id": "q1", "kind": "単一ページ",
     "question": "第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？",
     "evidence": ["lec02-main-p052"],
     "expected": "LoRAは元の重みWを固定し、小さな行列A・B（低ランクの差分）だけを学習する。QLoRAは元の重みを4bitに圧縮する"},
    {"id": "q2", "kind": "複数ページ",
     "question": "コンパクションとセッションをまたぐメモリの違いは？ 日々のメモは全部長期メモリになりますか？",
     "evidence": ["lec03-main-p013", "lec03-main-p039", "lec03-main-p040"],
     "expected": "コンパクションは同じセッション内で古い履歴を要約に置き換える。メモリは外の保存先に書き出し次のセッションで戻す。日々のメモは全部は残らず、基準を超えたものだけMEMORY.mdに移る"},
    {"id": "q3", "kind": "資料にない",
     "question": "今回作ったRAGの実測平均応答時間と正答率は？",
     "evidence": [],
     "expected": "講義資料には今回の実測ログがないので、確認できないと答える"},
    {"id": "q4", "kind": "前後ページが要る",
     "question": "第1回で説明された最終課題の概要と、お題の例を教えてください。",
     "evidence": ["lec01-main-p061", "lec01-main-p062"],
     "expected": "p.61：候補から選んでアプリ開発、第6回予告→第13回詳細、提出物は説明資料＋コード。p.62（「テーマ例は次のページ」）：講義の質問応答を支援するシステムのPoC"},
    {"id": "q5", "kind": "前後ページが要る",
     "question": "第2回のクイズ3（1日1万件の問い合わせの振り分け）の答えと、その理由は？",
     "evidence": ["lec02-main-p043"],
     "expected": "答えはB（小さなモデルで分類し、評価セットで精度とコストを確かめる）。決まった判断を大量にこなすなら小さなモデルがコスト＜効果を満たしやすい"},
]

HOMEWORK_MODES = ["rag", "topk10", "neighbors"]
EXERCISE_MODES = ["full", "rag", "tree", "graph"]
MODE_LABELS = {"rag": "ベクトル検索（top5・基準）", "topk10": "基礎：RAG_TOP_K=10",
               "neighbors": "実装：top5＋前後1ページ", "full": "全文投入", "tree": "Tree", "graph": "Graph"}

CITATION = re.compile(r"第\s*(\d+)\s*回\s*[・･、,]?\s*(?:PDF\s*)?p\.?\s*(\d+(?:\s*(?:[,，、]|[-–〜~])\s*(?:p\.?\s*)?\d+)*)")


def cited_pages(text: str) -> list[str]:
    """回答中の「第N回・PDF p.N」（p.51, 52 や p.51–52 も）をページIDにする。"""
    found = []
    for lecture, numbers in CITATION.findall(text):
        parts = re.split(r"\s*[,，、]\s*", numbers)
        for part in parts:
            part = re.sub(r"p\.?\s*", "", part)
            if re.search(r"[-–〜~]", part):
                a, b = (int(x) for x in re.split(r"\s*[-–〜~]\s*", part)[:2])
                pages = range(a, b + 1) if 0 <= b - a <= 10 else [a, b]
            else:
                pages = [int(part)]
            for page in pages:
                page_id = f"lec{int(lecture):02d}-main-p{page:03d}"
                if page_id not in found:
                    found.append(page_id)
    return found


def label(page_id: str) -> str:
    m = re.match(r"lec(\d+)-main-p(\d+)", page_id)
    return f"第{int(m[1])}回 p.{int(m[2])}" if m else page_id


@contextlib.contextmanager
def configured(mode: str):
    """mode に合わせて検索件数・ツールを切り替え、終わったら戻す。"""
    agent = agent_module.agent
    saved_top_k = retrieval.RAG_TOP_K
    retrieval.RAG_TOP_K = 10 if mode == "topk10" else 5
    if mode == "neighbors":
        ctx = agent.override(tools=[agent_module.NEIGHBOR_TOOL])
    elif mode == "tree":
        ctx = agent.override(instructions=agent_module.TREE_INSTRUCTIONS, tools=[tools.browse_tree])
    elif mode == "graph":
        ctx = agent.override(instructions=agent_module.GRAPH_INSTRUCTIONS, tools=[tools.search_graph])
    else:
        ctx = contextlib.nullcontext()
    try:
        with ctx:
            yield agent
    finally:
        retrieval.RAG_TOP_K = saved_top_k


def pages_from_return(part: ToolReturnPart) -> tuple[list[dict], str | None]:
    try:
        data = json.loads(part.content)
    except (TypeError, json.JSONDecodeError):
        return [], None
    if data.get("error"):
        return [], data["error"]
    if part.tool_name == "search_graph":
        rows = data.get("seeds", []) + data.get("expanded", [])
    elif part.tool_name == "browse_tree":
        node = data.get("node", {})
        rows = [{**node, "page_id": node["id"]}] if node.get("kind") == "page" else []
    else:
        rows = data.get("results", [])
    return [{"page_id": r["page_id"], "role": r.get("role", "hit"), "chars": len(r.get("content", ""))}
            for r in rows], None


def run_once(question: dict, mode: str, model) -> dict:
    with configured(mode) as agent:
        started = perf_counter()
        if mode == "full":
            with contextlib.redirect_stdout(io.StringIO()):
                result = retrieval.run_full_context(
                    agent, question["question"], model,
                    instructions=agent_module.FULL_CONTEXT_INSTRUCTIONS,
                    prompt_template=agent_module.FULL_CONTEXT_PROMPT)
        else:
            result = agent.run_sync(question["question"], model=model)
        elapsed = perf_counter() - started
    trace = io.StringIO()
    with contextlib.redirect_stdout(trace):
        agent_module.print_trace(result, elapsed)

    calls, returned, errors = [], [], []
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                calls.append({"tool": part.tool_name, "args": part.args_as_dict()})
            elif isinstance(part, ToolReturnPart):
                pages, error = pages_from_return(part)
                returned.append(pages)
                if error:
                    errors.append(error)
    retrieved = list(dict.fromkeys(p["page_id"] for pages in returned for p in pages))
    output = str(result.output)
    cited = cited_pages(output)
    usage = result.usage
    return {
        "question_id": question["id"], "mode": mode, "output": output,
        "tool_calls": calls, "returned_pages": returned, "retrieved": retrieved,
        "retrieved_chars": sum(p["chars"] for pages in returned for p in pages),
        "evidence_retrieved": [e for e in question["evidence"] if e in retrieved],
        "cited": cited, "evidence_cited": [e for e in question["evidence"] if e in cited],
        "cited_not_retrieved": [c for c in cited if mode != "full" and c not in retrieved],
        "tool_errors": errors, "seconds": round(elapsed, 2),
        "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
        "requests": usage.requests, "cost_usd": float(usage.cost) if usage.cost is not None else None,
        "trace": trace.getvalue(),
    }


def run_with_retry(question: dict, mode: str, model, tries: int = 4) -> dict:
    for attempt in range(1, tries + 1):
        try:
            record = run_once(question, mode, model)
        except ModelHTTPError as e:
            if e.status_code in (429, 503) and attempt < tries:
                print(f"  HTTP {e.status_code}。60秒待って再実行します（{attempt}/{tries}）")
                time.sleep(60)
                continue
            raise
        if any("レート制限" in e or "混み合" in e for e in record["tool_errors"]) and attempt < tries:
            print(f"  検索でレート制限。60秒待って再実行します（{attempt}/{tries}）")
            time.sleep(60)
            continue
        return record
    raise RuntimeError("再実行の上限に達しました")


def retrieval_only(question: dict) -> dict:
    """同じ検索語（質問文そのもの）で、検索器が返すページだけを比べる。埋め込みは1回だけ呼ぶ。"""
    saved = retrieval.RAG_TOP_K
    retrieval.RAG_TOP_K = 10
    try:
        top10 = retrieval.search(question["question"])
    finally:
        retrieval.RAG_TOP_K = saved
    top5 = top10[:5]
    neighbors = retrieval.add_neighbor_pages(top5, retrieval.load_pages())
    rows = {}
    for mode, results in (("rag", top5), ("topk10", top10), ("neighbors", neighbors)):
        ids = [r["page_id"] for r in results]
        rows[mode] = {"pages": [{"page_id": r["page_id"], "role": r.get("role", "hit"),
                                 "distance": round(r["distance"], 4) if "distance" in r else None}
                                for r in results],
                      "chars": sum(len(r["content"]) for r in results),
                      "evidence_found": [e for e in question["evidence"] if e in ids]}
    return {"question_id": question["id"], "query": question["question"], **rows}


def fmt_cost(value):
    return "算定不可" if value is None else f"${value:.6f}"


def write_report(meta: dict, retrievals: list[dict], runs: list[dict], path: Path) -> None:
    q_by_id = {q["id"]: q for q in QUESTIONS}
    lines = [f"# 第5回 宿題の比較結果（自動生成）", "",
             f"- 実行日時：{meta['executed_at']}", f"- 回答モデル：{meta['model']}",
             f"- 埋め込み：{meta['embedding_model']}（{meta['embedding_dimensions']}次元）",
             "- 対象資料：第1〜3回の本講義214ページ（全文投入だけは全9資料・438ページ）",
             "- 固定した条件：質問文・モデル・INSTRUCTIONS・ツール名。変えたのは mode の列だけ", ""]

    if retrievals:
        lines += ["## 1. 検索だけの比較（検索語＝質問文、埋め込みは同じ1回の結果を使う）", "",
                  "| 質問 | 方式 | ページ数 | 本文文字数 | 期待する根拠 | 取得ページ（太字＝根拠、*＝前後で追加）|",
                  "|---|---|---|---|---|---|"]
        for r in retrievals:
            q = q_by_id[r["question_id"]]
            for mode in ("rag", "topk10", "neighbors"):
                row = r[mode]
                pages = []
                for p in row["pages"]:
                    text = label(p["page_id"]) + ("*" if p["role"] == "neighbor" else "")
                    pages.append(f"**{text}**" if p["page_id"] in q["evidence"] else text)
                need = f"{len(row['evidence_found'])}/{len(q['evidence'])}" if q["evidence"] else "なし"
                lines.append(f"| {q['id']} {q['kind']} | {MODE_LABELS[mode]} | {len(row['pages'])} | "
                             f"{row['chars']:,} | {need} | {'、'.join(pages)} |")
        lines.append("")

    lines += ["## 2. エージェントの比較（--trace と同じ情報）", ""]
    for q in QUESTIONS:
        q_runs = [r for r in runs if r["question_id"] == q["id"]]
        if not q_runs:
            continue
        lines += [f"### {q['id']}（{q['kind']}）{q['question']}", "",
                  f"- 期待する根拠：{'、'.join(label(e) for e in q['evidence']) or '資料にない'}",
                  f"- 期待する答え：{q['expected']}", "",
                  "| 方式 | 検索語 | 取得ページ数／本文文字数 | 根拠の取得 | 根拠の引用 | 引用したページ | 時間（秒） | 入力／出力 tokens | 応答回数 | 推定費用 |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in q_runs:
            queries = "／".join(str(c["args"].get("query", c["args"].get("node_id", ""))) for c in r["tool_calls"]) or "（なし）"
            need = len(q["evidence"])
            got = f"{len(r['evidence_retrieved'])}/{need}" if need else "—"
            if r["mode"] == "full":
                got = "（全資料を入力）"
            cite = f"{len(r['evidence_cited'])}/{need}" if need else "—"
            pages = f"{len(r['retrieved'])}／{r['retrieved_chars']:,}" if r["mode"] != "full" else "全資料"
            lines.append(f"| {MODE_LABELS[r['mode']]} | {queries} | {pages} | {got} | {cite} | "
                         f"{'、'.join(label(c) for c in r['cited']) or 'なし'} | {r['seconds']} | "
                         f"{r['input_tokens']:,}／{r['output_tokens']:,} | {r['requests']} | {fmt_cost(r['cost_usd'])} |")
        lines.append("")
        for r in q_runs:
            note = ""
            if r["tool_errors"]:
                note += f"\n\n⚠ ツールのエラー：{r['tool_errors']}"
            if r["cited_not_retrieved"]:
                note += f"\n\n⚠ 取得していないのに引用したページ：{'、'.join(label(c) for c in r['cited_not_retrieved'])}"
            lines += [f"<details><summary>{MODE_LABELS[r['mode']]} の回答と --trace</summary>", "",
                      "```text", r["output"].strip(), "", r["trace"].strip(), "```", note, "", "</details>", ""]

    totals = {}
    for r in runs:
        t = totals.setdefault(r["mode"], {"n": 0, "seconds": 0.0, "in": 0, "out": 0, "cost": 0.0, "ev": 0, "need": 0})
        t["n"] += 1
        t["seconds"] += r["seconds"]
        t["in"] += r["input_tokens"]
        t["out"] += r["output_tokens"]
        t["cost"] += r["cost_usd"] or 0
        t["ev"] += len(r["evidence_retrieved"])
        t["need"] += len(q_by_id[r["question_id"]]["evidence"])
    if totals:
        lines += ["## 3. 合計", "", "| 方式 | 実行数 | 根拠の取得（合計） | 時間（秒） | 入力 tokens | 出力 tokens | 推定費用 |",
                  "|---|---|---|---|---|---|---|"]
        for mode, t in totals.items():
            lines.append(f"| {MODE_LABELS[mode]} | {t['n']} | {t['ev']}/{t['need']} | {t['seconds']:.2f} | "
                         f"{t['in']:,} | {t['out']:,} | ${t['cost']:.6f} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", default=",".join(q["id"] for q in QUESTIONS), help="例: q1,q2")
    parser.add_argument("--modes", default=",".join(HOMEWORK_MODES), help="rag,topk10,neighbors,full,tree,graph")
    parser.add_argument("--exercise", action="store_true", help="演習の表用に q1 を full,rag,tree,graph でも測る")
    parser.add_argument("--wait", type=float, default=6.0, help="実行の間の待ち秒数（無料枠のレート制限対策）")
    parser.add_argument("--skip-retrieval", action="store_true", help="検索だけの比較を省く")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    wanted = set(args.questions.split(","))
    questions = [q for q in QUESTIONS if q["id"] in wanted]
    modes = args.modes.split(",")
    unknown = set(modes) - set(MODE_LABELS)
    if unknown:
        parser.error(f"未知の mode: {unknown}")

    model = agent_module.build_model()
    meta = {"executed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "model": MODEL, "embedding_model": retrieval.EMBEDDING_MODEL,
            "embedding_dimensions": retrieval.EMBEDDING_DIMENSIONS}
    print(f"[model] {MODEL}")

    retrievals = []
    if not args.skip_retrieval:
        for q in questions:
            print(f"[検索のみ] {q['id']}")
            retrievals.append(retrieval_only(q))
            time.sleep(1)

    plan = [(q, m) for q in questions for m in modes]
    if args.exercise:
        q1 = QUESTIONS[0]
        plan += [(q1, m) for m in EXERCISE_MODES if (q1, m) not in plan]
    runs = []
    for i, (q, mode) in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] {q['id']} {MODE_LABELS[mode]}")
        record = run_with_retry(q, mode, model)
        print(f"  {record['seconds']}秒 / 入力 {record['input_tokens']:,} tokens / "
              f"根拠の取得 {len(record['evidence_retrieved'])}/{len(q['evidence'])} / "
              f"引用 {'、'.join(label(c) for c in record['cited']) or 'なし'}")
        runs.append(record)
        if i < len(plan):
            time.sleep(args.wait)

    args.out.mkdir(parents=True, exist_ok=True)
    data = {"meta": meta, "questions": questions, "retrieval_only": retrievals, "runs": runs}
    (args.out / "homework_runs.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(meta, retrievals, runs, args.out / "homework_report.md")
    print(f"\n保存しました: {args.out / 'homework_report.md'} と homework_runs.json")


if __name__ == "__main__":
    main()
