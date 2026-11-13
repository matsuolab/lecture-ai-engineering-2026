from types import SimpleNamespace

import pytest

from app import ask as ask_module


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        (SimpleNamespace(prompt_token_count=12, candidates_token_count=7), "[usage] input_tokens=12 output_tokens=7"),
        (None, "[usage] input_tokens=不明 output_tokens=不明"),
    ],
)
def test_ask_prints_token_usage(monkeypatch, capsys, usage, expected):
    class FakeClient:
        def __init__(self, api_key):
            self.models = self

        def generate_content(self, model, contents):
            return SimpleNamespace(text="answer", usage_metadata=usage)

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out.strip() == expected