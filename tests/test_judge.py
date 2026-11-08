"""第4回: 採点（app/judge.py）の配線テスト。API キーは使わない。

--model test と同じ偽モデル（規則で判定する FunctionModel）で、評価セット 10 件の
「採点 → 人のラベルとの比較 → 要確認・不一致の集計」が通ることを確かめる。
"""

import json

import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from app import judge
from app.judge import (
    ALL_CRITERIA,
    DEFAULT_CASES,
    DEFAULT_RUBRIC,
    build_judge,
    build_test_model,
    check_lecture_mark,
    generate_answers,
    judge_cases,
    load_labels,
    load_progress,
    overall,
    progress_key,
    read_jsonl,
    save_progress,
    summarize,
    write_jsonl,
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


# ---------------------------------------------------------------- 回答の生成（途中保存と再開）
def _three_cases(answers: list[str]) -> list[dict]:
    return [{"id": str(i), "question": f"質問{i}", "answer": a} for i, a in enumerate(answers)]


def test_generate_answers_only_fills_missing(tmp_path):
    path = tmp_path / "cases.jsonl"
    cases = _three_cases(["済み", "", ""])
    rows = generate_answers(cases, path, wait=0, model=TestModel(call_tools=[], custom_output_text="新しい回答"))
    assert [r["answer"] for r in rows] == ["済み", "新しい回答", "新しい回答"]
    assert [r["answer"] for r in read_jsonl(path)] == ["済み", "新しい回答", "新しい回答"]
    assert cases[1]["answer"] == ""  # 元の dict は書き換えない


def test_generate_answers_keeps_saved_rows_when_rate_limited(tmp_path):
    path = tmp_path / "cases.jsonl"
    calls = []

    def flaky(messages, info):
        calls.append(1)
        if len(calls) == 2:
            raise ModelHTTPError(status_code=429, model_name="test", body="quota")
        return ModelResponse(parts=[TextPart("生成した回答")])

    with pytest.raises(ModelHTTPError):
        generate_answers(_three_cases(["", "", ""]), path, wait=0, model=FunctionModel(flaky))
    assert [r["answer"] for r in read_jsonl(path)] == ["生成した回答", "", ""]

    # 再実行すると未生成の 2 件だけを生成する
    rows = generate_answers(read_jsonl(path), path, wait=0, model=FunctionModel(flaky))
    assert [r["answer"] for r in rows] == ["生成した回答"] * 3
    assert len(calls) == 4


def test_generate_answers_nothing_to_do_and_force(tmp_path, capsys):
    path = tmp_path / "cases.jsonl"
    cases = _three_cases(["a", "b", "c"])
    write_jsonl(path, cases)
    before = path.read_text(encoding="utf-8")

    def must_not_call(messages, info):
        raise AssertionError("モデルを呼んではいけない")

    rows = generate_answers(cases, path, wait=0, model=FunctionModel(must_not_call))
    assert rows == cases
    assert path.read_text(encoding="utf-8") == before
    assert "--force" in capsys.readouterr().out

    rows = generate_answers(cases, path, wait=0, force=True, model=TestModel(call_tools=[], custom_output_text="作り直し"))
    assert [r["answer"] for r in rows] == ["作り直し"] * 3


# ---------------------------------------------------------------- 採点の途中結果
def test_judge_cases_skips_done_and_saves_each_step():
    cases = read_jsonl(DEFAULT_CASES)
    agent = build_judge(build_test_model(), DEFAULT_RUBRIC.read_text(encoding="utf-8"))
    first = judge_cases(agent, cases[:1])
    saved = []

    verdicts = judge_cases(agent, cases, done=first, save=lambda v: saved.append(len(v)))
    assert set(verdicts) == {c["id"] for c in cases}
    assert verdicts[cases[0]["id"]] == first[cases[0]["id"]]
    assert saved == list(range(2, 11))  # 未採点 9 件ぶん、1 件ごとに保存


def test_progress_roundtrip_depends_on_key(tmp_path):
    path = tmp_path / "r.partial.json"
    key = progress_key("test", "基準", DEFAULT_CASES)
    save_progress(path, key, {"1": {"x": 1}})
    assert load_progress(path, key) == {"1": {"x": 1}}
    assert load_progress(path, progress_key("test", "別の基準", DEFAULT_CASES)) == {}
    assert load_progress(path, progress_key("other", "基準", DEFAULT_CASES)) == {}
    assert load_progress(tmp_path / "none.json", key) == {}


def _main_args(out):
    return ["--model", "test", "--cases", str(DEFAULT_CASES), "--labels", str(INSTRUCTOR_LABELS), "--out", str(out)]


def test_main_removes_partial_and_resumes(tmp_path):
    out = tmp_path / "r.json"
    judge.main(_main_args(out))
    assert not out.with_suffix(".partial.json").exists()
    result = json.loads(out.read_text(encoding="utf-8"))
    assert len(result["verdicts"]) == 10

    # 一致する途中結果（1 件分）を置くと、その 1 件はそのまま使われる
    cid = read_jsonl(DEFAULT_CASES)[0]["id"]
    marker = {k: {"reason": "前回の結果", "verdict": "pass"} for k, _ in ALL_CRITERIA}
    rubric = DEFAULT_RUBRIC.read_text(encoding="utf-8")
    save_progress(out.with_suffix(".partial.json"), progress_key("test", rubric, DEFAULT_CASES), {cid: marker})
    judge.main(_main_args(out))
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["verdicts"][cid] == marker
    assert len(result["verdicts"]) == 10
    assert not out.with_suffix(".partial.json").exists()
