"""素のLLMの対話ループのテスト（APIキーもLLMも使わない）。"""

import sys
from types import SimpleNamespace

from app import ask as ask_module


def test_main_reuses_one_chat_for_follow_up_questions(monkeypatch, capsys):
    questions = []

    class FakeChat:
        def send_message(self, question):
            questions.append(question)
            return SimpleNamespace(text=f"回答: {question}", usage_metadata=None)

    chat = FakeChat()

    class FakeClient:
        class chats:
            @staticmethod
            def create(*, model):
                assert model == ask_module.MODEL
                return chat

    def make_client(api_key):
        assert api_key == "test-key"
        return FakeClient()

    def fake_input(prompt):
        assert "空行" in prompt
        return next(answers)

    monkeypatch.setattr(ask_module.genai, "Client", make_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "最初の質問"])
    answers = iter(["続きの質問", ""])
    monkeypatch.setattr("builtins.input", fake_input)

    ask_module.main()

    output = capsys.readouterr().out
    assert questions == ["最初の質問", "続きの質問"]
    assert "回答: 最初の質問" in output
    assert "回答: 続きの質問" in output
