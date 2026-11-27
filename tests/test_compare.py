from types import SimpleNamespace
from itertools import cycle

from app.compare import RateLimits, compare, load_rate_limits


class FakeClient:
    def __init__(self):
        self.models = self
        self.calls = []

    def generate_content(self, *, model, contents):
        self.calls.append((model, contents))
        return SimpleNamespace(
            text=f"answer from {model}",
            usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=5),
        )


def test_compare_runs_every_model_question_pair_and_prints_metrics(monkeypatch, capsys):
    client = FakeClient()
    durations = cycle([1.0, 1.4, 2.0, 2.5])
    monkeypatch.setattr("app.compare.time.perf_counter", lambda: next(durations))
    limits = RateLimits(rpm=15, tpm=1_000_000, rpd=1500)

    compare(
        client,
        ["gemini-a", "gemini-b"],
        ["Q1", "Q2"],
        {"gemini-a": limits, "gemini-b": limits},
    )

    output = capsys.readouterr().out
    assert client.calls == [
        ("gemini-a", "Q1"),
        ("gemini-a", "Q2"),
        ("gemini-b", "Q1"),
        ("gemini-b", "Q2"),
    ]
    assert "RPM: 15 / TPM（入力）: 1000000 / RPD: 1500" in output
    assert "入力: 20 tokens / 出力: 10 tokens" in output
    assert "RPM 2/15 requests（残り 13）" in output


def test_model_specific_limits_override_shared_limits(monkeypatch):
    monkeypatch.setenv("AIE_RPM_LIMIT", "15")
    monkeypatch.setenv("AIE_GEMINI_3_5_FLASH_LITE_RPM_LIMIT", "8")
    monkeypatch.setenv("AIE_TPM_LIMIT", "1000000")
    monkeypatch.setenv("AIE_RPD_LIMIT", "1500")

    limits = load_rate_limits("gemini-3.5-flash-lite")

    assert limits == RateLimits(rpm=8, tpm=1_000_000, rpd=1500)