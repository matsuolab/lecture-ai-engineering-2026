from types import SimpleNamespace

from app import ask


def test_ask_displays_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="answer",
    )

    class FakeModels:
        def generate_content(self, *, model, contents):
            assert model == ask.MODEL
            assert contents == "question"
            return response

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(ask.genai, "Client", lambda *, api_key: FakeClient())
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("question") == "answer"
    output = capsys.readouterr().out
    assert "[elapsed] " in output
    assert "[tokens] input=12 output=34" in output


def test_main_runs_each_model_and_question_sequentially(monkeypatch, capsys):
    calls = []

    def fake_ask(question, *, model):
        calls.append((model, question))
        return "answer"

    monkeypatch.setattr(ask, "ask", fake_ask)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.ask",
            "--model",
            "model-a",
            "--model",
            "model-b",
            "question-1",
            "question-2",
        ],
    )

    ask.main()

    assert calls == [
        ("model-a", "question-1"),
        ("model-a", "question-2"),
        ("model-b", "question-1"),
        ("model-b", "question-2"),
    ]
    assert capsys.readouterr().out.count("answer") == 4
