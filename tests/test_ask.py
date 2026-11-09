import json
from types import SimpleNamespace

from google.genai import types

import app.ask as ask_module


class FakeChat:
    def __init__(self, history, answer):
        self.history = list(history)
        self.answer = answer

    def send_message(self, question):
        self.history.extend(
            [
                types.Content(role="user", parts=[types.Part(text=question)]),
                types.Content(role="model", parts=[types.Part(text=self.answer)]),
            ]
        )
        return SimpleNamespace(text=self.answer, usage_metadata=None)

    def get_history(self):
        return self.history


def test_ask_persists_and_restores_conversation_history(tmp_path, monkeypatch, capsys):
    history_path = tmp_path / "chat_history.json"
    created_chats = []
    clock_values = iter([10.0, 12.0, 30.0, 31.25])

    class FakeClient:
        @property
        def chats(self):
            return self

        def create(self, *, model, history, config):
            chat = FakeChat(history, f"回答{len(created_chats) + 1}")
            created_chats.append((chat, history))
            return chat

    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(clock_values))

    assert ask_module.ask("最初の質問", history_path) == "回答1"
    assert ask_module.ask("続きの質問", history_path) == "回答2"

    assert capsys.readouterr().out.splitlines() == [
        "[応答時間] 2.00秒",
        "[応答時間] 1.25秒",
    ]
    assert len(created_chats[1][1]) == 2
    assert json.loads(history_path.read_text(encoding="utf-8")) == [
        {"role": "user", "text": "最初の質問"},
        {"role": "model", "text": "回答1"},
        {"role": "user", "text": "続きの質問"},
        {"role": "model", "text": "回答2"},
    ]
