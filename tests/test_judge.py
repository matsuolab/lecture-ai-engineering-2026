"""第4回: 採点（app/judge.py）の配線テスト。API キーは使わない。

--model test と同じ偽モデル（規則で判定する FunctionModel）で、評価セット 10 件の
「採点 → 人のラベルとの比較 → 要確認・不一致の集計」が通ることを確かめる。
"""

import json
import sys
from types import SimpleNamespace

from app import judge
from app.judge import (
    ALL_CRITERIA,
    DEFAULT_CASES,
    DEFAULT_RUBRIC,
    build_judge,
    build_test_model,
    check_lecture_mark,
    judge_cases,
    load_labels,
    overall,
    read_jsonl,
    summarize,
)

INSTRUCTOR_LABELS = judge.ROOT / "lectures" / "04" / "reference" / "labels_instructor.jsonl"


def test_lecture_mark_is_checked_by_code():
    assert check_lecture_mark("LoRA は…\n\n関係する回：第2回") == "pass"
    assert check_lecture_mark("第2回で扱う LoRA は…\n\n以上です。") == "fail"  # 末尾に無ければ fail
    assert check_lecture_mark("") == "fail"


def test_overall_requires_all_required_criteria():
    base = {"grounding": "pass", "scope": "pass", "hint": "pass", "lecture_mark": "pass", "clarity": "fail"}
    assert overall(base) == "pass"  # 分かりやすさは総合に入れない
    assert overall({**base, "hint": "fail"}) == "fail"
    assert overall({**base, "grounding": "unsure"}) == "unsure"


def test_cases_and_rubric_are_consistent():
    cases = read_jsonl(DEFAULT_CASES)
    assert len(cases) == 10
    assert len({c["id"] for c in cases}) == 10
    for c in cases:
        assert c["question"] and c["answer"] and c["reference"]["expected"]
    rubric = DEFAULT_RUBRIC.read_text(encoding="utf-8")
    for key, name in ALL_CRITERIA[:-1]:  # 回の表示はコードで判定するので rubric には書かない
        assert f"{name}（{key}）" in rubric
    labels = load_labels(INSTRUCTOR_LABELS)
    assert set(labels) == {c["id"] for c in cases}


def test_judge_pipeline_with_fake_model():
    cases = read_jsonl(DEFAULT_CASES)
    labels = load_labels(INSTRUCTOR_LABELS)
    agent = build_judge(build_test_model(), DEFAULT_RUBRIC.read_text(encoding="utf-8"))

    verdicts = judge_cases(agent, cases)
    assert set(verdicts) == {c["id"] for c in cases}
    for v in verdicts.values():
        for key, _ in ALL_CRITERIA:
            assert v[key]["verdict"] in ("pass", "fail", "unsure")
            assert v[key]["reason"]

    summary = summarize(cases, verdicts, labels)
    assert summary["n"] == 10
    # unsure にした項目は一致率の分母から外れ、要確認に入る
    excluded = sum(p["total"] - p["compared"] for p in summary["per_criterion"].values())
    assert excluded == len(summary["review"])
    assert summary["coverage"]["covered"] + len({r["id"] for r in summary["review"]}) == 10
    for m in summary["mismatches"]:
        assert m["kind"] in ("見逃し", "過検出")


def test_main_saves_each_completed_case(tmp_path, monkeypatch):
    output = tmp_path / "judge_result.json"
    original_judge_cases = judge.judge_cases
    saved_counts = []

    def check_progress(agent, cases, wait=0.0, on_case_complete=None):
        def save_and_check(verdicts):
            on_case_complete(verdicts)
            saved = json.loads(output.read_text(encoding="utf-8"))
            expected_count = len(saved_counts) + 1
            assert len(saved["verdicts"]) == expected_count
            assert "summary" not in saved
            saved_counts.append(expected_count)

        return original_judge_cases(agent, cases, wait, save_and_check)

    monkeypatch.setattr(judge, "judge_cases", check_progress)
    judge.main([
        "--model", "test",
        "--labels", str(INSTRUCTOR_LABELS),
        "--out", str(output),
    ])

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved_counts == list(range(1, 11))
    assert len(saved["verdicts"]) == 10
    assert saved["summary"]["n"] == 10


def test_generate_saves_cases_after_each_answer(tmp_path, monkeypatch):
    cases_path = tmp_path / "cases.jsonl"
    cases = [
        {"id": "01", "question": "first", "answer": ""},
        {"id": "02", "question": "second", "answer": ""},
    ]
    judge.write_jsonl(cases_path, cases)

    writes = []
    original_write_jsonl = judge.write_jsonl

    def track_write_jsonl(path, rows):
        original_write_jsonl(path, rows)
        if path == cases_path:
            writes.append(judge.read_jsonl(cases_path))

    def run_sync(question, model):
        return SimpleNamespace(output=f"answer: {question}")

    fake_app_agent = SimpleNamespace(
        agent=SimpleNamespace(run_sync=run_sync),
        build_model=lambda: object(),
    )
    monkeypatch.setitem(sys.modules, "app.agent", fake_app_agent)
    monkeypatch.setattr(judge, "write_jsonl", track_write_jsonl)
    waits = []
    monkeypatch.setattr(judge.time, "sleep", waits.append)

    judge.main(["--generate", "--cases", str(cases_path)])

    assert waits == [30.0]
    assert [[case["answer"] for case in snapshot] for snapshot in writes] == [
        ["answer: first", ""],
        ["answer: first", "answer: second"],
    ]
    assert judge.read_jsonl(cases_path) == [
        {"id": "01", "question": "first", "answer": "answer: first"},
        {"id": "02", "question": "second", "answer": "answer: second"},
    ]
