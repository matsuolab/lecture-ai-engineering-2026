from types import SimpleNamespace

import app.compare as compare_module


def test_comparison_runs_each_model_and_question_without_history(monkeypatch, capsys):
    requests = []

    class FakeChat:
        def __init__(self, model):
            self.model = model

        def send_message(self, question):
            requests.append((self.model, question))
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3,
                    candidates_token_count=5,
                ),
                text=f"{self.model}の回答",
            )

    class FakeClient:
        @property
        def chats(self):
            return self

        def create(self, *, model, config):
            return FakeChat(model)

    monkeypatch.setattr(compare_module.genai, "Client", lambda api_key: FakeClient())
    monkeypatch.setattr(compare_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        compare_module.time,
        "perf_counter",
        iter([1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]).__next__,
    )
    monkeypatch.setattr(compare_module.time, "sleep", lambda seconds: None)

    trials = compare_module.run_comparison(
        ["model-a", "model-b"],
        ["質問1", "質問2"],
    )

    assert requests == [
        ("model-a", "質問1"),
        ("model-b", "質問1"),
        ("model-a", "質問2"),
        ("model-b", "質問2"),
    ]
    assert [trial.elapsed_seconds for trial in trials] == [0.5, 1.0, 1.0, 1.0]
    assert all(trial.input_tokens == 3 and trial.output_tokens == 5 for trial in trials)
    assert "比較結果" in capsys.readouterr().out


def test_comparison_stops_after_rate_limit(monkeypatch, capsys):
    monkeypatch.setattr(compare_module.genai, "Client", lambda api_key: object())
    monkeypatch.setattr(compare_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        compare_module,
        "run_trial",
        lambda client, model, question: compare_module.Trial(
            model=model,
            question=question,
            elapsed_seconds=0.1,
            input_tokens=None,
            output_tokens=None,
            answer=None,
            error="レート制限に達しました",
            status_code=429,
        ),
    )
    monkeypatch.setattr(
        compare_module.time,
        "sleep",
        lambda seconds: (_ for _ in ()).throw(AssertionError("sleep should not run")),
    )

    trials = compare_module.run_comparison(
        ["model-a", "model-b"],
        ["質問1", "質問2"],
    )

    assert len(trials) == 1
    assert "残りの試行を中止" in capsys.readouterr().out
