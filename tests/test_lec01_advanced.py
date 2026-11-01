"""APIキー不要。mockの出力を実際のGemini結果と誤認しないこと。"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import lec01_advanced as exp


@pytest.fixture
def glossary():
    return {
        "homework-levels": "基礎（講義内容の確認）、実装（自分でコードを書く）、発展（調査や試行）の3段階で、いずれか1つで完了。",
        "lec-start-tag": "各回の開始時点を示すGitタグ。例lec03-start。",
        "default-model": "既定モデルはgemini-3.5-flash-lite。無料枠のレート制限と安定性のため。",
        "lora": "LoRAは低ランク行列で一部パラメータを学習するPEFTの手法。",
    }


def make_response(text="正解です", prompt=10, output=20, thought=3, total=33):
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt,
            candidates_token_count=output,
            thoughts_token_count=thought,
            total_token_count=total,
        ),
    )


class FakeModels:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        result = self.responses.pop(0) if self.responses else make_response()
        if isinstance(result, Exception):
            raise result
        return result


class FakeClient:
    def __init__(self, responses=None):
        self.models = FakeModels(responses)


def single(tmp_path, **kwargs):
    return exp.Config(models=("fake",), questions=("homework-levels",), repeats=1,
                      pause_seconds=0.0, output_dir=tmp_path, **kwargs)


def test_plan_has_all_conditions_three_times_and_is_deterministic(tmp_path):
    config = exp.Config(models=("m1", "m2"), repeats=3, output_dir=tmp_path)
    a = exp.plan_trials(config)
    b = exp.plan_trials(config)
    assert a == b
    assert len(a) == 54
    assert len({trial.key for trial in a}) == len(a)
    assert {t.condition for t in a} == {"baseline", "irrelevant", "grounded"}


@pytest.mark.parametrize("condition", exp.CONDITIONS)
def test_context_controls_do_not_leak_target_gold(condition, glossary):
    text = exp.build_prompt("homework-levels", condition, glossary)
    assert "AIE2026" in text
    if condition == "grounded":
        assert glossary["homework-levels"] in text
    else:
        assert glossary["homework-levels"] not in text
    if condition == "irrelevant":
        assert glossary["lora"] in text


def test_token_counts_missing_and_zero_are_distinct():
    r = SimpleNamespace(usage_metadata=SimpleNamespace(prompt_token_count=0, candidates_token_count=None))
    assert exp.response_tokens(r)["input_tokens"] == 0
    assert exp.response_tokens(r)["output_tokens"] is None
    assert exp.response_tokens(SimpleNamespace()) == {
        "input_tokens": None, "output_tokens": None, "thought_tokens": None, "total_tokens": None
    }


def test_call_once_records_monotonic_latency_and_hash(tmp_path, glossary):
    client = FakeClient([make_response(text="ok")])
    trial = exp.Trial("fake", "homework-levels", 1, "grounded")
    ticks = iter((5.0, 5.25))
    result, answer = exp.call_once(client, trial, single(tmp_path), glossary, clock=lambda: next(ticks))
    assert result["status"] == "ok"
    assert result["latency_seconds"] == 0.25
    assert result["total_tokens"] == 33
    assert result["response_sha256"] and answer == "ok"
    assert client.models.calls[0]["config"]["max_output_tokens"] == 1024
    assert "API_KEY" not in str(result)


def test_empty_response_is_not_success(tmp_path, glossary):
    client = FakeClient([make_response(text="")])
    r, answer = exp.call_once(client, exp.Trial("fake", "homework-levels", 1, "baseline"), single(tmp_path), glossary)
    assert r["status"] == "empty_response"
    assert answer == ""


def test_api_errors_are_sanitized_and_continue(tmp_path, glossary):
    error = RuntimeError("Secret leaked: key=1234")
    client = FakeClient([error, make_response(), make_response()])
    exp.run(single(tmp_path), client, glossary, sleeper=lambda _: None)
    rows = exp._read_rows(tmp_path / "measurements.csv")
    assert len(rows) == 3
    assert "Secret" not in (tmp_path / "measurements.csv").read_text()
    assert "Secret" not in (tmp_path / "summary.md").read_text()
    assert any(r["status"] == "error" for r in rows)
    assert (tmp_path / "comparison.svg").exists()


def test_resume_skips_success_and_retries_failed(tmp_path, glossary):
    config = single(tmp_path)
    exp.run(config, FakeClient([RuntimeError("transient"), make_response(), make_response()]), glossary, sleeper=lambda _: None)
    second = FakeClient([make_response()])
    exp.run(config, second, glossary, sleeper=lambda _: None)
    assert len(second.models.calls) == 1
    third = FakeClient()
    exp.run(config, third, glossary, sleeper=lambda _: None)
    assert len(third.models.calls) == 0
    assert len(exp._read_rows(tmp_path / "measurements.csv")) == 4
    assert len(exp._read_rows(tmp_path / "review.csv")) == 3
    assert len(exp._summary_data(tmp_path)[0]) == 3


def test_prevents_mixing_different_configurations(tmp_path, glossary):
    exp.run(single(tmp_path), FakeClient(), glossary, sleeper=lambda _: None)
    with pytest.raises(ValueError, match="設定が異なります"):
        exp.run(exp.Config(models=("different",), questions=("homework-levels",),
                           repeats=1, pause_seconds=0, output_dir=tmp_path), FakeClient(), glossary)


def test_review_scores_survive_reanalysis(tmp_path, glossary):
    exp.run(single(tmp_path), FakeClient(), glossary, sleeper=lambda _: None)
    path = tmp_path / "review.csv"
    rows = exp._read_rows(path)
    rows[0]["accuracy_score"] = "2"
    rows[0]["hallucination"] = "no"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=exp.REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    exp.build_review(tmp_path, glossary)
    assert exp._read_rows(path)[0]["accuracy_score"] == "2"
    summary = exp.analyze(tmp_path)
    assert "2.00 (n=1)" in summary


def test_invalid_config_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        exp.plan_trials(exp.Config(repeats=0, output_dir=tmp_path))
    with pytest.raises(ValueError):
        exp.plan_trials(exp.Config(pause_seconds=float("nan"), output_dir=tmp_path))
    with pytest.raises(ValueError):
        exp.build_prompt("unknown", "baseline", {})


def test_svg_escapes_injected_model_labels(tmp_path):
    stats = [{"model": '<script>alert("x")</script>', "condition": "baseline", "latency": [1.0], "total": [10.0]}]
    file = tmp_path / "chart.svg"
    exp.chart_svg(stats, file)
    data = file.read_text()
    assert "<script>" not in data
    assert "&lt;script&gt;" in data


def test_csv_persistence_is_valid_utf8(tmp_path):
    exp.save_csv_row(tmp_path / "out.csv", {"model": "日本語", "question_id": "q", "repetition": 1, "condition": "baseline", "status": "ok"})
    rows = exp._read_rows(tmp_path / "out.csv")
    assert rows[0]["model"] == "日本語"


def test_plan_cli_is_offline(tmp_path, monkeypatch, capsys, glossary):
    monkeypatch.setattr(exp, "load_glossary", lambda: glossary)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    exp.main(["plan", "--models", "fake", "--questions", "homework-levels", "--repeats", "1", "--output-dir", str(tmp_path)])
    assert "planned calls: 3" in capsys.readouterr().out
    assert not list(tmp_path.iterdir())


def test_duplicate_models_and_questions_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="重複"):
        exp.plan_trials(exp.Config(models=("m", "m"), output_dir=tmp_path))
    with pytest.raises(ValueError, match="重複"):
        exp.plan_trials(exp.Config(questions=("homework-levels", "homework-levels"), output_dir=tmp_path))


def test_sync_answer_does_not_overwrite_surrounding_text(tmp_path):
    file = tmp_path / "answer.md"
    file.write_text("before\n<!-- EXPERIMENT_RESULTS_START -->old<!-- EXPERIMENT_RESULTS_END -->\nafter", encoding="utf-8")
    exp.sync_answer("new report", file)
    data = file.read_text(encoding="utf-8")
    assert data.startswith("before") and data.endswith("after")
    assert "new report" in data and "old" not in data


def test_sync_answer_rejects_missing_markers(tmp_path):
    file = tmp_path / "answer.md"
    file.write_text("no markers", encoding="utf-8")
    with pytest.raises(ValueError, match="マーカー"):
        exp.sync_answer("report", file)
    assert file.read_text(encoding="utf-8") == "no markers"


def test_paired_score_difference_is_counted(tmp_path, glossary):
    exp.run(single(tmp_path), FakeClient(), glossary, sleeper=lambda _: None)
    file = tmp_path / "review.csv"
    reviews = exp._read_rows(file)
    for r in reviews:
        r["accuracy_score"] = "2" if r["condition"] == "grounded" else "0"
        r["hallucination"] = "no"
    with file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=exp.REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(reviews)
    summary = exp.analyze(tmp_path)
    assert "grounded - baseline" in summary
    assert "2.00 (n=1)" in summary
    assert "0.0%" in summary


def test_bad_float_is_not_coerced_to_zero():
    assert exp._number("") is None
    assert exp._number("nan") is None
    assert exp._number("bad") is None
    assert exp._number("0") == 0
