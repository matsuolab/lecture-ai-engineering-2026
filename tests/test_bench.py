import csv
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

bench = import_module("lectures.01.bench")


def test_run_trial_records_elapsed_time_and_token_counts():
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        )
    )
    clock = iter((1.0, 1.25))

    row = bench.run_trial(client, "model-a", "question", 1, lambda: next(clock))

    assert row["seconds"] == 0.25
    assert row["input_tokens"] == 12
    assert row["output_tokens"] == 34
    assert row["status"] == "ok"
    client.models.generate_content.assert_called_once_with(
        model="model-a", contents="question"
    )


def test_run_trial_leaves_missing_usage_tokens_blank():
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(usage_metadata=None)
    clock = iter((1.0, 1.1))

    row = bench.run_trial(client, "model-a", "question", 1, lambda: next(clock))

    assert row["input_tokens"] == ""
    assert row["output_tokens"] == ""
    assert row["status"] == "ok"


def test_run_benchmark_records_errors_and_continues():
    client = Mock()
    client.models.generate_content.side_effect = [
        RuntimeError("unavailable"),
        SimpleNamespace(
            usage_metadata=SimpleNamespace(
                prompt_token_count=3,
                candidates_token_count=4,
            )
        ),
    ]
    clock = iter((1.0, 1.2, 2.0, 2.3))
    waits = []

    rows = bench.run_benchmark(
        client,
        models=(("model-a", 1),),
        questions=("first", "second"),
        sleep_fn=waits.append,
        perf_counter=lambda: next(clock),
    )

    assert len(rows) == 2
    assert rows[0]["status"] == "error: RuntimeError"
    assert rows[0]["seconds"] == pytest.approx(0.2)
    assert rows[1]["status"] == "ok"
    assert rows[1]["output_tokens"] == 4
    assert client.models.generate_content.call_count == 2
    assert waits == [5]


def test_write_csv_writes_all_fields_and_blank_tokens(tmp_path):
    rows = [
        {
            "model": "model-a",
            "question": "質問",
            "run": 1,
            "seconds": 0.5,
            "input_tokens": "",
            "output_tokens": "",
            "status": "error: RuntimeError",
        }
    ]
    path = tmp_path / "bench.csv"

    bench.write_csv(rows, path)

    with path.open(encoding="utf-8", newline="") as csv_file:
        result = list(csv.DictReader(csv_file))
    assert result[0]["model"] == "model-a"
    assert result[0]["input_tokens"] == ""
    assert result[0]["status"] == "error: RuntimeError"


def test_summarize_calculates_model_averages_and_failures():
    rows = [
        {"model": "model-a", "seconds": 1.0, "output_tokens": 10, "status": "ok"},
        {"model": "model-a", "seconds": 3.0, "output_tokens": 30, "status": "ok"},
        {
            "model": "model-a",
            "seconds": 2.0,
            "output_tokens": "",
            "status": "error: RuntimeError",
        },
    ]

    assert bench.summarize(rows) == {
        "model-a": {
            "average_seconds": 2.0,
            "average_output_tokens": 20,
            "failures": 1,
        }
    }