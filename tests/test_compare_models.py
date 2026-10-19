from types import SimpleNamespace

import pytest
from google.genai import errors

from scripts.compare_models import print_comparison, run_comparison, summarize


def test_run_comparison_records_latency_and_token_counts(monkeypatch):
    responses = iter([
        SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=5, candidates_token_count=10),
            text="回答A",
        ),
        SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=6, candidates_token_count=8),
            text="回答B",
        ),
    ])
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: next(responses))
    )
    clock = iter([1.0, 1.4, 2.0, 2.8])
    monkeypatch.setattr("scripts.compare_models.time.perf_counter", lambda: next(clock))

    results = run_comparison(client, ["model-a", "model-b"], "質問", 1, interval_seconds=0)
    summaries = summarize(results)

    assert summaries["model-a"]["elapsed_seconds"] == pytest.approx(0.4)
    assert summaries["model-a"]["input_tokens"] == 5
    assert summaries["model-a"]["output_tokens"] == 10
    assert summaries["model-b"]["elapsed_seconds"] == pytest.approx(0.8)
    assert summaries["model-b"]["output_tokens"] == 8


def test_print_comparison_reports_metric_differences(capsys):
    print_comparison({
        "model-a": {"elapsed_seconds": 1.0, "input_tokens": 10, "output_tokens": 20},
        "model-b": {"elapsed_seconds": 2.0, "input_tokens": 12, "output_tokens": 30},
    })

    output = capsys.readouterr().out
    assert "出力トークン数の差: 10 tokens (33.3%)" in output
    assert "[判定] model-a は最速かつ出力トークン数が最少" in output


def test_run_comparison_waits_between_requests_and_retries_rate_limits(monkeypatch):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=5, candidates_token_count=10),
        text="回答",
    )
    calls = 0

    def generate_content(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise errors.APIError(429, {"error": {"message": "rate limit"}})
        return response

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    waits = []
    monkeypatch.setattr("scripts.compare_models.time.sleep", waits.append)
    monkeypatch.setattr("scripts.compare_models.random.uniform", lambda start, end: 0)

    results = run_comparison(
        client,
        ["model-a", "model-b"],
        "質問",
        1,
        interval_seconds=4,
        max_retries=1,
    )

    assert len(results) == 2
    assert calls == 3
    assert waits == [10, 4]