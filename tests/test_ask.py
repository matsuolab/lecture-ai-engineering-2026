"""app.ask の会話履歴テスト（LLMもAPIキーも使わない）。"""

import sys
from types import SimpleNamespace

from google.genai import types

from app import ask


def _content(role: str, text: str) -> types.Content:
    return types.Content.model_validate({"role": role, "parts": [{"text": text}]})


def test_load_history_returns_empty_when_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ask, "HISTORY_PATH", tmp_path / ".ask_history.json")

    assert ask.load_history() == []


def test_history_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(ask, "HISTORY_PATH", tmp_path / ".ask_history.json")
    history = [_content("user", "最初の質問"), _content("model", "最初の回答")]

    ask.save_history(history)

    assert ask.load_history() == history


def test_main_reuses_history_and_can_reset_without_api_key(tmp_path, monkeypatch, capsys):
    history_path = tmp_path / ".ask_history.json"
    monkeypatch.setattr(ask, "HISTORY_PATH", history_path)
    history_seen_by_chat = []
    models_seen = []
    api_keys_seen = []

    class FakeChat:
        def __init__(self, history):
            self.history = list(history)

        def send_message(self, question):
            self.history.extend([_content("user", question), _content("model", "回答")])
            return SimpleNamespace(usage_metadata=None, text="回答")

        def get_history(self):
            return self.history

    class FakeChats:
        def create(self, model, history):
            models_seen.append(model)
            history_seen_by_chat.append(list(history))
            return FakeChat(history)

    class FakeClient:
        def __init__(self, api_key):
            api_keys_seen.append(api_key)
            self.chats = FakeChats()

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "1つ目の質問"])
    ask.main()

    assert history_seen_by_chat == [[]]
    assert models_seen == [ask.MODEL]
    assert api_keys_seen == ["test-key"]
    assert len(ask.load_history()) == 2

    monkeypatch.setattr(sys, "argv", ["app.ask", "2つ目の質問"])
    ask.main()

    assert len(history_seen_by_chat[1]) == 2
    assert models_seen == [ask.MODEL, ask.MODEL]
    assert api_keys_seen == ["test-key", "test-key"]
    assert len(ask.load_history()) == 4
    assert "回答" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["app.ask", "--reset-history"])
    ask.main()

    assert not history_path.exists()
    assert "[history] cleared" in capsys.readouterr().out
