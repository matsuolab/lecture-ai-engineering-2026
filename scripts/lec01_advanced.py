"""AIE2026 Lecture 1: reproducible latency/token and groundedness experiment.

In the official lecture repository run:
    uv run python -m scripts.lec01_advanced plan
    uv run python -m scripts.lec01_advanced run
    uv run python -m scripts.lec01_advanced analyze

This module uses the pinned google-genai version supplied by the course repo.
Experiments are independent single-turn calls, not multi-turn conversations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS: dict[str, tuple[str, str]] = {
    "homework-levels": ("AIE2026の宿題の3レベルを具体的に説明してください。", "homework-levels"),
    "lec-start-tag": ("AIE2026で使うlecNN-startタグとは何ですか？", "lec-start-tag"),
    "default-model": ("AIE2026の演習の既定モデルと、その採用理由を説明してください。", "default-model"),
}
CONDITIONS = ("baseline", "irrelevant", "grounded")
DEFAULT_MODELS = ("gemini-3.5-flash-lite", "gemini-3.6-flash")
CSV_COLUMNS = (
    "model", "question_id", "repetition", "condition", "status", "error_status",
    "latency_seconds", "input_tokens", "output_tokens", "thought_tokens", "total_tokens",
    "response_sha256", "timestamp_utc",
)
REVIEW_COLUMNS = (
    "model", "question_id", "repetition", "condition", "response", "reference_definition",
    "accuracy_score", "hallucination", "notes",
)


@dataclass(frozen=True)
class Config:
    models: tuple[str, ...] = DEFAULT_MODELS
    questions: tuple[str, ...] = tuple(QUESTIONS)
    repeats: int = 3
    pause_seconds: float = 4.0
    seed: int = 2026
    max_output_tokens: int = 1024
    output_dir: Path = ROOT / "outputs" / "lec01_advanced"


@dataclass(frozen=True)
class Trial:
    model: str
    question_id: str
    repetition: int
    condition: str

    @property
    def key(self) -> tuple[str, str, int, str]:
        return self.model, self.question_id, self.repetition, self.condition


def validate(config: Config) -> None:
    if not config.models or not config.questions:
        raise ValueError("モデルと質問を1つ以上指定してください")
    if len(set(config.models)) != len(config.models) or len(set(config.questions)) != len(config.questions):
        raise ValueError("モデル名と質問IDを重複させないでください")
    if any(q not in QUESTIONS for q in config.questions):
        raise ValueError("未知の質問IDです")
    if config.repeats < 1 or config.repeats > 100:
        raise ValueError("repeatsは1〜100で指定してください")
    if config.pause_seconds < 0 or not math.isfinite(config.pause_seconds):
        raise ValueError("pauseは0以上の有限値を指定してください")
    if config.max_output_tokens < 64:
        raise ValueError("max_output_tokensは64以上にしてください")


def load_glossary(path: Path = ROOT / "data" / "glossary.json") -> dict[str, str]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    definitions = {item["id"]: item["definition"] for item in data["terms"]}
    absent = {qid for qid in QUESTIONS if qid not in definitions}
    if absent:
        raise ValueError(f"用語集に必須の定義がありません: {sorted(absent)}")
    return definitions


def irrelevant_definition(definitions: dict[str, str], question_id: str) -> str:
    """同じ質問の正解を含まない、無関係な定義を利用する陰性対照。"""
    # 3質問で内容が重ならない学習方法（LoRA）の定義を統一して使う。
    # 質問の対象自体には直接関連しないが、文字数は正解定義と一致しない。
    candidate_id = "lora"
    if candidate_id == question_id or candidate_id not in definitions:
        raise ValueError("陰性対照の定義を取得できません")
    return definitions[candidate_id]


def build_prompt(question_id: str, condition: str, definitions: dict[str, str]) -> str:
    if question_id not in QUESTIONS or condition not in CONDITIONS:
        raise ValueError("不正な質問または実験条件です")
    question = QUESTIONS[question_id][0]
    common = (
        "次の質問に日本語で200字以内で回答してください。"
        "不明な点は推測せず、不明と明示してください。\n"
    )
    if condition == "baseline":
        return common + "質問: " + question
    definition = (
        definitions[question_id]
        if condition == "grounded"
        else irrelevant_definition(definitions, question_id)
    )
    return (
        common
        + "参考資料（この資料は講座の用語集からの抜粋です。" 
        + "質問に関係する場合のみ使用してください）:\n"
        + definition
        + "\n質問: " + question
    )


def plan_trials(config: Config) -> list[Trial]:
    """再現可能な順序にシャッフルする（ブロックごとに条件を混ぜる）。"""
    validate(config)
    rng = random.Random(config.seed)
    trials = []
    for repetition in range(1, config.repeats + 1):
        block = [
            Trial(model=model, question_id=q, repetition=repetition, condition=condition)
            for model in config.models for q in config.questions for condition in CONDITIONS
        ]
        rng.shuffle(block)
        trials.extend(block)
    return trials


def _token(response: Any, field: str) -> int | None:
    usage = getattr(response, "usage_metadata", None)
    number = getattr(usage, field, None)
    return int(number) if number is not None else None


def response_tokens(response: Any) -> dict[str, int | None]:
    return {
        "input_tokens": _token(response, "prompt_token_count"),
        "output_tokens": _token(response, "candidates_token_count"),
        "thought_tokens": _token(response, "thoughts_token_count"),
        "total_tokens": _token(response, "total_token_count"),
    }


def call_once(client: Any, trial: Trial, config: Config, definitions: dict[str, str], clock: Any = time.perf_counter) -> tuple[dict[str, Any], str]:
    prompt = build_prompt(trial.question_id, trial.condition, definitions)
    result: dict[str, Any] = {
        "model": trial.model,
        "question_id": trial.question_id,
        "repetition": trial.repetition,
        "condition": trial.condition,
        "status": "ok",
        "error_status": "",
        "latency_seconds": None,
        "input_tokens": None,
        "output_tokens": None,
        "thought_tokens": None,
        "total_tokens": None,
        "response_sha256": "",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    response_text = ""
    started = clock()
    try:
        # SDKの自動再試行を利用する。APIキー・生の例外文字列は保存しない。
        response = client.models.generate_content(
            model=trial.model,
            contents=prompt,
            config={"max_output_tokens": config.max_output_tokens},
        )
        response_text = getattr(response, "text", None) or ""
        result.update(response_tokens(response))
        result["response_sha256"] = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        if not response_text.strip():
            result["status"] = "empty_response"
    except Exception as error:
        # リクエストに失敗しても実験全体を停止しない。
        # 例外の本文には秘密情報が混ざりうるため記録しない。
        result["status"] = "error"
        status = getattr(error, "code", None)
        result["error_status"] = str(status) if isinstance(status, int) else type(error).__name__
    finally:
        result["latency_seconds"] = round(clock() - started, 6)
    return result, response_text


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def save_csv_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow({key: row.get(key) for key in CSV_COLUMNS})
        file.flush()
        os.fsync(file.fileno())


def save_response(path: Path, trial: Trial, text: str) -> None:
    record = {"model": trial.model, "question_id": trial.question_id,
              "repetition": trial.repetition, "condition": trial.condition, "response": text}
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()
        os.fsync(file.fileno())


def run(config: Config, client: Any, definitions: dict[str, str], sleeper: Any = time.sleep) -> None:
    """中断後に再開可能。成功した計測は再実行しない。"""
    validate(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    path = config.output_dir / "measurements.csv"
    existing = _read_rows(path)
    successful = {
        (r["model"], r["question_id"], int(r["repetition"]), r["condition"])
        for r in existing if r["status"] in ("ok", "empty_response")
    }
    manifest_file = config.output_dir / "manifest.json"
    manifest = {
        "models": list(config.models), "questions": list(config.questions),
        "repeats": config.repeats, "seed": config.seed,
        "conditions": list(CONDITIONS), "max_output_tokens": config.max_output_tokens,
        "generation_config": "SDK defaults except max_output_tokens; no temperature override",
        "glossary_sha256": hashlib.sha256((ROOT / "data" / "glossary.json").read_bytes()).hexdigest() if (ROOT / "data" / "glossary.json").exists() else "test",
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    if manifest_file.exists():
        previous = json.loads(manifest_file.read_text(encoding="utf-8"))
        for key in ("models", "questions", "repeats", "seed", "conditions", "max_output_tokens", "glossary_sha256"):
            if previous[key] != manifest[key]:
                raise ValueError(f"既存実験と設定が異なります: {key}。別の --output-dir を指定してください。")
    else:
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pending = [trial for trial in plan_trials(config) if trial.key not in successful]
    print(f"計画数: {len(plan_trials(config))}, 今回の実行数: {len(pending)}")
    for i, trial in enumerate(pending, start=1):
        if i > 1:
            sleeper(config.pause_seconds)
        metrics, answer = call_once(client, trial, config, definitions)
        save_csv_row(path, metrics)
        save_response(config.output_dir / "responses.jsonl", trial, answer)
        print(f"[{i}/{len(pending)}] {trial.model} | {trial.question_id} | {trial.condition} "
              f"| {metrics['status']} | {metrics['latency_seconds']}s", flush=True)
    build_review(config.output_dir, definitions)
    analyze(config.output_dir)


def build_review(output_dir: Path, definitions: dict[str, str]) -> None:
    """手動評価用CSVを生成。既存の採点済みデータは上書きしない。"""
    path = output_dir / "review.csv"
    old = {
        (r["model"], r["question_id"], r["repetition"], r["condition"]): r
        for r in _read_rows(path)
    }
    records = []
    responses_file = output_dir / "responses.jsonl"
    if not responses_file.exists():
        return
    # 再開時の失敗→成功による重複は、最後の成功した応答に揃える。
    last: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for line in responses_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = (r["model"], r["question_id"], str(r["repetition"]), r["condition"])
        last[key] = r
    for key, response in last.items():
        if not response["response"].strip():
            continue
        old_row = old.get(key, {})
        # 出力が変わったケースは以前の採点を引き継がない。
        same_response = old_row.get("response") == response["response"]
        records.append({
            "model": key[0], "question_id": key[1], "repetition": key[2], "condition": key[3],
            "response": response["response"], "reference_definition": definitions[key[1]],
            "accuracy_score": old_row.get("accuracy_score", "") if same_response else "",
            "hallucination": old_row.get("hallucination", "") if same_response else "",
            "notes": old_row.get("notes", "") if same_response else "",
        })
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _fmt(values: list[float], digits: int = 2) -> str:
    return f"{statistics.mean(values):.{digits}f}" if values else "NA"


def _summary_data(output_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    latest: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in _read_rows(output_dir / "measurements.csv"):
        key = (row["model"], row["question_id"], row["repetition"], row["condition"])
        if row["status"] == "ok" or key not in latest or latest[key]["status"] != "ok":
            latest[key] = row
    rows = list(latest.values())
    review = _read_rows(output_dir / "review.csv")
    groups = sorted({(r["model"], r["condition"]) for r in rows})
    scored = {(r["model"], r["question_id"], r["repetition"], r["condition"]): r for r in review}
    stats = []
    for model, condition in groups:
        group = [r for r in rows if r["model"] == model and r["condition"] == condition]
        good = [r for r in group if r["status"] == "ok"]
        vals = [(_number(r["latency_seconds"]), _number(r["input_tokens"]),
                 _number(r["output_tokens"]), _number(r["total_tokens"])) for r in good]
        scores = []
        hallucinations = []
        for row in good:
            key = (row["model"], row["question_id"], row["repetition"], row["condition"])
            review_row = scored.get(key, {})
            accuracy = review_row.get("accuracy_score", "")
            if accuracy in ("0", "1", "2"):
                scores.append(int(accuracy))
            if review_row.get("hallucination") in ("yes", "no"):
                hallucinations.append(review_row["hallucination"] == "yes")
        stats.append({"model": model, "condition": condition, "n": len(good), "attempts": len(group),
                      "latency": [a for a, _, _, _ in vals if a is not None],
                      "input": [b for _, b, _, _ in vals if b is not None],
                      "output": [c for _, _, c, _ in vals if c is not None],
                      "total": [d for _, _, _, d in vals if d is not None],
                      "scores": scores, "hallucinations": hallucinations})
    return rows, review, stats


def chart_svg(stats: list[dict[str, Any]], output_path: Path) -> None:
    """追加ライブラリなしで平均レイテンシと平均総トークンの棒グラフを保存。"""
    labels = [f"{s['model']} / {s['condition']}" for s in stats]
    height = max(310, 100 + len(labels) * 48)
    width = 1050
    fragments = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                 '<rect width="100%" height="100%" fill="#ffffff"/>',
                 '<text x="28" y="35" font-family="sans-serif" font-size="18" font-weight="bold">AIE2026 Lecture 1 - Measured means (successful calls only)</text>']
    for x_origin, kind, caption, color in ((445, "latency", "Latency (s)", "#2454a6"), (740, "total", "Total tokens", "#0f766e")):
        fragments.append(f'<text x="{x_origin}" y="64" font-family="sans-serif" font-size="14">{caption}</text>')
        vals = [statistics.mean(s[kind]) if s[kind] else 0.0 for s in stats]
        max_v = max(vals, default=0.0) or 1.0
        for idx, v in enumerate(vals):
            y = 84 + idx * 48
            bar_w = max(0.0, 175.0 * v / max_v)
            fragments.append(f'<rect x="{x_origin}" y="{y}" width="{bar_w:.1f}" height="21" rx="3" fill="{color}"/>')
            fragments.append(f'<text x="{x_origin + 180}" y="{y + 16}" font-family="sans-serif" font-size="12">{v:.2f}</text>')
    for idx, label in enumerate(labels):
        y = 99 + idx * 48
        fragments.append(f'<text x="28" y="{y}" font-family="sans-serif" font-size="12">{escape(label)}</text>')
    fragments.append(f'<text x="28" y="{height - 20}" font-family="sans-serif" font-size="11">NA/missing values are excluded. This chart alone does not establish statistical significance.</text>')
    fragments.append('</svg>')
    output_path.write_text("\n".join(fragments) + "\n", encoding="utf-8")


def analyze(output_dir: Path) -> str:
    rows, review, stats = _summary_data(output_dir)
    if not rows:
        raise ValueError("計測結果がありません。先にrunを実行してください。")
    lines = [
        "# 第1回 発展＋Plus α 実験レポート（自動集計）", "",
        "## 実験の前提", "",
        "- 全呼び出しは独立した単発リクエスト。回答に会話履歴は含めない。",
        "- baseline: 資料なし / irrelevant: 無関係なLoRAの定義 / grounded: 対象の正解定義を付加。",
        "- モデルの思考設定は既定値。モデル間の内部推論量が揃うとは限らない。",
        "- latencyはSDK呼び出し全体（SDKの自動リトライを含む）の壁時計時間。",
        "- サンプル数が小さく、下表は**記述統計**。有意差・因果効果は断定しない。",
        "- 正確性は手動採点。スコア2=重要事実が正確、1=一部正しい、0=誤り/不足/不明。",
        "- hallucination=yesは誤った事実を断定した回答。『不明』は誤答でもハルシネーションではない。",
        "", "## モデル・条件別結果", "",
        "| モデル | 条件 | 成功/試行 | 平均秒 | 中央値秒 | 標準偏差秒 | 平均入力token | 平均出力token | 平均総token | 平均正確性(0-2) | ハルシネーション率 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in stats:
        median = f"{statistics.median(s['latency']):.2f}" if s["latency"] else "NA"
        accuracy = f"{statistics.mean(s['scores']):.2f} (n={len(s['scores'])})" if s["scores"] else "未採点"
        sd = f"{statistics.stdev(s['latency']):.2f}" if len(s["latency"]) > 1 else "NA"
        hallu = f"{100*statistics.mean(s['hallucinations']):.1f}% (n={len(s['hallucinations'])})" if s["hallucinations"] else "未採点"
        lines.append(f"| {s['model']} | {s['condition']} | {s['n']}/{s['attempts']} | {_fmt(s['latency'])} | {median} | {sd} | {_fmt(s['input'], 1)} | {_fmt(s['output'], 1)} | {_fmt(s['total'], 1)} | {accuracy} | {hallu} |")
    lines.extend(["", "## ペア比較（同一モデル・質問・反復の対応差）", "",
                  "| モデル | 差分条件 | レイテンシペア数 | 平均秒差 | 平均総token差 | 正確性差(0-2) |", "|---|---|---:|---:|---:|---:|"])
    reviews_by_key = {(r["model"], r["question_id"], r["repetition"], r["condition"]): r for r in review}
    for model in sorted({r["model"] for r in rows}):
        good = {(r["question_id"], r["repetition"], r["condition"]): r for r in rows
                if r["model"] == model and r["status"] == "ok"}
        for control in ("baseline", "irrelevant"):
            latency_diffs, token_diffs, accuracy_diffs = [], [], []
            for q, rep, condition in list(good):
                if condition != control or (q, rep, "grounded") not in good:
                    continue
                b, g = good[(q, rep, control)], good[(q, rep, "grounded")]
                la, lb = _number(b["latency_seconds"]), _number(g["latency_seconds"])
                ta, tb = _number(b["total_tokens"]), _number(g["total_tokens"])
                if la is not None and lb is not None:
                    latency_diffs.append(lb - la)
                if ta is not None and tb is not None:
                    token_diffs.append(tb - ta)
                base_review = reviews_by_key.get((model, q, rep, control), {})
                ground_review = reviews_by_key.get((model, q, rep, "grounded"), {})
                if base_review.get("accuracy_score") in ("0", "1", "2") and ground_review.get("accuracy_score") in ("0", "1", "2"):
                    accuracy_diffs.append(int(ground_review["accuracy_score"]) - int(base_review["accuracy_score"]))
            score_label = f"{_fmt(accuracy_diffs)} (n={len(accuracy_diffs)})" if accuracy_diffs else "未採点"
            lines.append(f"| {model} | grounded - {control} | {len(latency_diffs)} | {_fmt(latency_diffs)} | {_fmt(token_diffs, 1)} | {score_label} |")
    errors = [r for r in rows if r["status"] != "ok"]
    if errors:
        lines.extend(["", "## エラー・未完了", "", "| モデル | 質問 | 条件 | 反復 | 状態 | ステータス |", "|---|---|---|---:|---|---|"])
        for r in errors:
            lines.append(f"| {r['model']} | {r['question_id']} | {r['condition']} | {r['repetition']} | {r['status']} | {r['error_status']} |")
    lines.extend(["", "## 評価上の制約", "",
                  "- 陰性対照は文字数・トークン数を厳密に一致させていないため、コンテキスト長の影響を完全には分離できない。",
                  "- 質問数と反復数が少ない。設問を増やし、実行順と日を変えた追試が必要。",
                  "- grounded条件は正答定義を直接付与するオラクル対照であり、検索精度を含むRAGの評価ではない。",
                  "- 出力トークン数と総トークン数は別物。モデルの思考トークンが含まれる可能性がある。",
                  "- キー/予算/無料枠/レート制限はプロジェクトとモデルの条件に依存し、1回の実験で一般化できない。",
                  ""])
    summary = "\n".join(lines)
    (output_dir / "summary.md").write_text(summary, encoding="utf-8")
    chart_svg(stats, output_dir / "comparison.svg")
    return summary


def sync_answer(summary: str, answer_path: Path = ROOT / "lectures" / "01" / "answer.md") -> None:
    """明示したマーカー間だけを書き換え、提出レポートの実測欄を更新する。"""
    start_tag = "<!-- EXPERIMENT_RESULTS_START -->"
    end_tag = "<!-- EXPERIMENT_RESULTS_END -->"
    document = answer_path.read_text(encoding="utf-8")
    if document.count(start_tag) != 1 or document.count(end_tag) != 1:
        raise ValueError("answer.md に必要なマーカーがありません。手動編集を保護するため自動更新しません")
    left, rest = document.split(start_tag, 1)
    _, right = rest.split(end_tag, 1)
    answer_path.write_text(left + start_tag + "\n\n" + summary.strip() + "\n\n" + end_tag + right, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AIE2026 Lec01 Advanced + Alpha")
    parser.add_argument("mode", nargs="?", choices=("plan", "run", "analyze"), default="plan")
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--questions", nargs="+", choices=tuple(QUESTIONS), default=list(QUESTIONS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--pause", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "lec01_advanced")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = Config(models=tuple(args.models), questions=tuple(args.questions),
                    repeats=args.repeats, pause_seconds=args.pause, seed=args.seed,
                    output_dir=args.output_dir)
    validate(config)
    if args.mode == "analyze":
        report = analyze(config.output_dir)
        sync_answer(report)
        print(report)
        return
    definitions = load_glossary()
    if args.mode == "plan":
        print(f"Models: {config.models}; questions: {config.questions}; repeats: {config.repeats}")
        print(f"Conditions: {CONDITIONS}; planned calls: {len(plan_trials(config))}")
        print("APIを呼び出さない計画確認モードです。")
        return
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY がありません。Codespaces secretで設定してください（キーを貼り付けない）。")
    from google import genai
    client = genai.Client(api_key=key)
    try:
        run(config, client, definitions)
        sync_answer((config.output_dir / "summary.md").read_text(encoding="utf-8"))
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    main()
