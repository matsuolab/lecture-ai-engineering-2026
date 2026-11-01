from types import SimpleNamespace

import app.ask as ask_module


def test_compare_models_sends_same_question_and_collects_metrics(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, *, model, contents):
            calls.append((model, contents))
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=12,
                    candidates_token_count=34,
                ),
                text=f"{model} の回答",
            )

    fake_client = SimpleNamespace(models=FakeModels())
    monkeypatch.setattr(
        ask_module,
        "genai",
        SimpleNamespace(Client=lambda *, api_key: fake_client),
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    times = iter((1.0, 1.5, 2.0, 2.75, 3.0, 4.0))
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(times))

    results = ask_module.compare_models("共通の質問", ("model-a", "model-b", "model-c"))

    assert calls == [
        ("model-a", "共通の質問"),
        ("model-b", "共通の質問"),
        ("model-c", "共通の質問"),
    ]
    assert [result.elapsed_seconds for result in results] == [0.5, 0.75, 1.0]
    assert [(result.input_tokens, result.output_tokens) for result in results] == [
        (12, 34),
        (12, 34),
        (12, 34),
    ]
    assert [result.text for result in results] == [
        "model-a の回答",
        "model-b の回答",
        "model-c の回答",
    ]
