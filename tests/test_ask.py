from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
    )

    class FakeClient:
        def __init__(self, api_key):
            self.models = SimpleNamespace(generate_content=lambda **kwargs: response)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out == "[tokens] input=12 output=7\n"