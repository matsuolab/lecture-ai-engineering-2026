from types import SimpleNamespace

from google.genai import errors

import app.benchmark as bench


def _response(prompt, candidates, thoughts=None):
    usage = SimpleNamespace(
        prompt_token_count=prompt,
        candidates_token_count=candidates,
        thoughts_token_count=thoughts,
        total_token_count=prompt + candidates + (thoughts or 0),
    )
    return SimpleNamespace(text="回答", usage_metadata=usage)


class FakeClient:
    """呼ばれるたびに outcomes を順に返す（例外なら投げる）偽クライアント。"""

    def __init__(self, outcomes):
        self.calls = []
        outcomes = iter(outcomes)

        def generate_content(**kwargs):
            self.calls.append(kwargs)
            outcome = next(outcomes)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        self.models = SimpleNamespace(generate_content=generate_content)


def _clock(*times):
    it = iter(times)
    return lambda: next(it)


def test_measure_records_latency_and_tokens():
    client = FakeClient([_response(10, 40, thoughts=5)])
    r = bench.measure(client, "m", "質問", clock=_clock(1.0, 3.0))

    assert r.ok
    assert r.latency_s == 2.0
    assert (r.input_tokens, r.output_tokens, r.thoughts_tokens, r.total_tokens) == (10, 40, 5, 55)
    assert r.output_tokens_per_s == 20.0
    assert client.calls[0]["config"] is None


def test_measure_passes_temperature():
    client = FakeClient([_response(1, 1)])
    bench.measure(client, "m", "q", temperature=0.0, clock=_clock(0.0, 1.0))
    assert client.calls[0]["config"].temperature == 0.0


def test_measure_records_rate_limit_error_instead_of_raising():
    client = FakeClient([errors.APIError(429, {"error": {"message": "quota"}})])
    r = bench.measure(client, "m", "q", clock=_clock(0.0, 0.5))

    assert not r.ok
    assert r.error.startswith("429")
    assert r.output_tokens_per_s is None


def test_run_benchmark_covers_all_combinations_and_summarizes(capsys):
    client = FakeClient([_response(10, 20)] * 3 + [errors.APIError(429, {})] + [_response(10, 30)] * 4)
    slept = []
    results = bench.run_benchmark(client, ["a", "b"], ["q1", "q2"], repeat=2, interval=1.5, sleep=slept.append)

    assert len(results) == 8
    assert [c["model"] for c in client.calls] == ["a"] * 4 + ["b"] * 4
    assert slept == [1.5] * 7  # 最初の呼び出しの前は待たない

    rows = {(r["model"], r["question"]): r for r in bench.summarize(results)}
    assert rows[("a", "q2")]["ok"] == 1 and rows[("a", "q2")]["errors"] == 1
    assert rows[("b", "q1")]["output_mean"] == 30
    assert "a | q2 | 1 | 1" in bench.format_summary(list(rows.values()))


def test_write_csv(tmp_path):
    results = [bench.Measurement("m", "q", 1, 2.0, 10, 40, None, 50)]
    path = tmp_path / "out.csv"
    bench.write_csv(str(path), results)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("model,question,run,latency_s")
    assert lines[1].endswith(",20.0")
