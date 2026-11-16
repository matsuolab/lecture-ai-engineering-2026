import json
from types import SimpleNamespace

from app import ask as ask_module


class FakeModels:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []

    def generate_content(self, *, model, contents):
        self.calls.append({"model": model, "contents": contents})
        return SimpleNamespace(text=next(self.answers), usage_metadata=None)


def test_ask_persists_and_reuses_conversation_history(tmp_path, monkeypatch):
    history_file = tmp_path / ".ask_history.json"
    models = FakeModels(["最初の回答", "続きの回答"])
    monkeypatch.setattr(ask_module, "HISTORY_FILE", history_file)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda *, api_key: SimpleNamespace(models=models),
    )

    assert ask_module.ask("最初の質問") == "最初の回答"
    assert ask_module.ask("続けて質問") == "続きの回答"

    assert models.calls[0]["contents"] == [
        {"role": "user", "parts": [{"text": "最初の質問"}]},
    ]
    assert models.calls[1]["contents"] == [
        {"role": "user", "parts": [{"text": "最初の質問"}]},
        {"role": "model", "parts": [{"text": "最初の回答"}]},
        {"role": "user", "parts": [{"text": "続けて質問"}]},
    ]
    assert json.loads(history_file.read_text(encoding="utf-8")) == [
        {"role": "user", "parts": [{"text": "最初の質問"}]},
        {"role": "model", "parts": [{"text": "最初の回答"}]},
        {"role": "user", "parts": [{"text": "続けて質問"}]},
        {"role": "model", "parts": [{"text": "続きの回答"}]},
    ]
