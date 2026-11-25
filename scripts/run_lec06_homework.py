"""第6回 宿題（基礎・実装）と演習を、同じモデルでまとめて実行し、結果を保存する。

    uv run python scripts/run_lec06_homework.py              # 宿題（基礎・実装）
    uv run python scripts/run_lec06_homework.py --exercise   # 演習の STEP 1〜4 も実行する

宿題（実装）では、範囲外になる質問を、make_quiz の 3 つの知らせ方で比べる。
    return      分かりやすいメッセージを return で返す（app/tools.py の make_quiz。提出する実装）
    raise       同じメッセージの例外（ValueError）を、そのまま投げる
    tool-error  同じメッセージを、MCP の ToolError（ツールの失敗）として返す
名前・説明文・INSTRUCTIONS は同じで、違うのは「範囲外の知らせ方」だけ。

出力（lectures/06/results/）
    homework_runs.json     各実行の回答・ツール呼び出し・ツールの戻り値／エラー・時間・トークン数
    homework_report.md     上をまとめた表（answer.md へ転記する元）
    server_stderr.log      用語集サーバーが出したエラー表示（raise で、サーバー側に何が残るかを見る）
"""

import argparse
import contextlib
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from fastmcp import Client  # noqa: E402
from pydantic_ai import Agent, capture_run_messages  # noqa: E402
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior  # noqa: E402
from pydantic_ai.mcp import MCPToolset, StdioTransport  # noqa: E402
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart  # noqa: E402

from app import mcp_agent  # noqa: E402
from app.config import MODEL  # noqa: E402

OUT_DIR = ROOT / "lectures/06/results"
MODES = ["return", "raise", "tool-error"]
MODE_LABELS = {"return": "return（提出する実装）", "raise": "raise（ValueError のまま）",
               "tool-error": "ToolError"}

HOMEWORK = [
    {"id": "b1", "level": "基礎", "question": "第2回では何を学びますか？", "modes": ["return"],
     "check": "glossary_get_lecture_summary が lecture=2 で呼ばれる"},
    {"id": "i1", "level": "実装・範囲内", "question": "第2回のクイズを2問作って", "modes": ["return"],
     "check": "glossary_make_quiz が lecture=2, count=2 で呼ばれ、問題だけを出す"},
    {"id": "i2", "level": "実装・範囲外（存在しない回）", "question": "第99回のクイズを作って", "modes": MODES,
     "check": "第1〜13回であること、作れる回を伝える"},
    {"id": "i3", "level": "実装・範囲外（用語がない回）", "question": "第5回のクイズを作って", "modes": MODES,
     "check": "第5回の用語はまだないこと、作れる回を伝える"},
    {"id": "i4", "level": "実装・範囲外（問題数）", "question": "第2回のクイズを10問作って", "modes": MODES,
     "check": "問題数は1〜5であることを伝える（または5問以内で作り直す）"},
]

EXERCISE = [
    {"id": "s2", "level": "演習 STEP 2", "question": "AIE2026の講座の宿題にある「3レベル」とは何ですか？"},
    {"id": "s3", "level": "演習 STEP 3", "question": "https://modelcontextprotocol.io/ の冒頭を日本語で3行に要約して"},
    {"id": "s4", "level": "演習 STEP 4", "question": "AWSのドキュメントを検索して、Amazon S3 のバージョニングを2行で説明して"},
]


def glossary_agent(mode: str, log_file) -> Agent:
    """用語集サーバーだけを、指定した知らせ方で起動するエージェント（app/mcp_agent.py と同じ組み立て）。"""
    args = ["run", "python", "-m", "app.mcp_server"] + ([] if mode == "return" else ["--quiz-errors", mode])
    transport = StdioTransport("uv", args, cwd=str(ROOT), log_file=log_file)
    toolset = MCPToolset(Client(transport, mode="legacy")).prefixed("glossary")
    return Agent(instructions=mcp_agent.INSTRUCTIONS, toolsets=[toolset])


def list_tools_text(agent: Agent) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        mcp_agent.print_tools(agent)
    return out.getvalue().strip()


def run_once(agent: Agent, question: str, model) -> dict:
    started = perf_counter()
    error = None
    with capture_run_messages() as messages:
        try:
            result = agent.run_sync(question, model=model)
            messages, output, usage = result.all_messages(), str(result.output), result.usage
        except UnexpectedModelBehavior as e:
            output, usage, error = None, None, f"{type(e).__name__}: {e}"
    elapsed = perf_counter() - started
    events = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                events.append({"kind": "tool call", "tool": part.tool_name, "args": part.args_as_dict()})
            elif isinstance(part, ToolReturnPart):
                events.append({"kind": "tool return", "tool": part.tool_name, "content": str(part.content)})
            elif isinstance(part, RetryPromptPart) and part.tool_name:
                # モデルに実際に渡る文（"Fix the errors and try again." まで含む）
                events.append({"kind": "tool error", "tool": part.tool_name, "content": part.model_response()})
    return {
        "output": output, "run_error": error, "events": events, "seconds": round(elapsed, 2),
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "requests": usage.requests if usage else None,
    }


def run_with_retry(agent: Agent, question: str, model, tries: int = 4) -> dict:
    for attempt in range(1, tries + 1):
        try:
            return run_once(agent, question, model)
        except ModelHTTPError as e:
            if e.status_code in (429, 503) and attempt < tries:
                print(f"  HTTP {e.status_code}。60秒待って再実行します（{attempt}/{tries}）")
                time.sleep(60)
                continue
            raise
    raise RuntimeError("再実行の上限に達しました")


def trace_lines(record: dict, limit: int = 400) -> list[str]:
    lines = []
    for e in record["events"]:
        if e["kind"] == "tool call":
            lines.append(f"[tool call]   {e['tool']}({e['args']})")
        else:
            text = e["content"].replace("\n", "\\n")
            lines.append(f"[{e['kind']}] {e['tool']} -> {text[:limit]}{'…' if len(text) > limit else ''}")
    if record["run_error"]:
        lines.append(f"[run error]   {record['run_error'][:limit]}")
    else:
        lines.append(f"[usage] 入力 {record['input_tokens']:,} tokens / 出力 {record['output_tokens']:,} tokens"
                     f" / モデル応答 {record['requests']} 回 / {record['seconds']} 秒")
    return lines


def summary_row(q: dict, mode: str, r: dict) -> str:
    calls = [f"{e['tool'].removeprefix('glossary_')}({', '.join(f'{k}={v}' for k, v in e['args'].items())})"
             for e in r["events"] if e["kind"] == "tool call"]
    kinds = [e["kind"].replace("tool ", "") for e in r["events"] if e["kind"] != "tool call"]
    if r["run_error"]:
        outcome = "**実行が止まった**"
    else:
        outcome = (r["output"] or "").strip().replace("\n", " ")
        outcome = outcome[:110] + ("…" if len(outcome) > 110 else "")
    tokens = "—" if r["input_tokens"] is None else f"{r['input_tokens']:,}／{r['output_tokens']:,}"
    return (f"| {q['id']} | {MODE_LABELS.get(mode, mode)} | {'、'.join(calls) or 'なし'} | {'、'.join(kinds) or '—'} | "
            f"{r['requests'] or '—'} | {tokens} | {outcome} |")


def write_report(meta: dict, tool_lists: dict, runs: list[dict], path: Path) -> None:
    lines = ["# 第6回 宿題・演習の実行結果（自動生成）", "",
             f"- 実行日時：{meta['executed_at']}", f"- 回答モデル：{meta['model']}",
             "- 固定した条件：質問文・モデル・INSTRUCTIONS・ツールの名前と説明文。宿題（実装）で変えたのは make_quiz の範囲外の知らせ方だけ",
             "- 各質問・各方式1回ずつ", ""]
    for title, text in tool_lists.items():
        lines += [f"## ツール一覧（{title}）", "", "```text", text, "```", ""]
    lines += ["## まとめ", "",
              "| 質問 | 知らせ方 | ツール呼び出し | 戻り方 | 応答回数 | 入力／出力 tokens | 回答（冒頭） |",
              "|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(summary_row(r["question"], r["mode"], r))
    lines.append("")
    for r in runs:
        q = r["question"]
        lines += [f"### {q['id']}（{q['level']}）{MODE_LABELS.get(r['mode'], r['mode'])}：{q['question']}", ""]
        if q.get("check"):
            lines += [f"- 確かめること：{q['check']}", ""]
        lines += ["```text", "--- 回答 ---", (r["output"] or "（回答なし）").strip(), "", "--- trace ---",
                  *trace_lines(r), "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--exercise", action="store_true", help="演習の STEP 1〜4（fetch・AWS を含む）も実行する")
    parser.add_argument("--only", default="", help="宿題の質問IDを絞る（例: i2,i3）")
    parser.add_argument("--wait", type=float, default=5.0, help="実行の間の待ち秒数（無料枠のレート制限対策）")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    model = mcp_agent.build_model()
    meta = {"executed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "model": MODEL}
    print(f"[model] {MODEL}")

    tool_lists, runs = {}, []
    wanted = set(filter(None, args.only.split(",")))
    plan = [(q, m) for q in HOMEWORK if not wanted or q["id"] in wanted for m in q["modes"]]
    with open(args.out / "server_stderr.log", "w", encoding="utf-8") as log:
        tool_lists["宿題：用語集サーバー"] = list_tools_text(glossary_agent("return", log))
        if args.exercise:
            full = mcp_agent.build_mcp_agent()
            tool_lists["演習 STEP 1〜4：app/mcp_servers.json"] = "\n".join(
                mcp_agent.describe_servers()) + "\n" + list_tools_text(full)
            plan += [(q, "exercise") for q in EXERCISE]
        for i, (q, mode) in enumerate(plan, 1):
            print(f"[{i}/{len(plan)}] {q['id']} {MODE_LABELS.get(mode, mode)}：{q['question']}")
            log.write(f"\n===== {q['id']} {mode} =====\n")
            log.flush()
            agent = mcp_agent.build_mcp_agent() if mode == "exercise" else glossary_agent(mode, log)
            record = run_with_retry(agent, q["question"], model)
            for line in trace_lines(record, limit=120):
                print("  " + line)
            runs.append({"question": q, "mode": mode, **record})
            if i < len(plan):
                time.sleep(args.wait)

    (args.out / "homework_runs.json").write_text(
        json.dumps({"meta": meta, "tool_lists": tool_lists, "runs": runs}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    write_report(meta, tool_lists, runs, args.out / "homework_report.md")
    print(f"\n保存しました: {args.out / 'homework_report.md'}")


if __name__ == "__main__":
    main()
