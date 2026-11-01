import builtins
import sys
from types import SimpleNamespace

import app.ask as ask_module


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return SimpleNamespace(
            text=f"回答: {question}",
            usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=4),
        )


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()
        self.created_models = []

    class Chats:
        def __init__(self, client):
            self.client = client

        def create(self, *, model):
            self.client.created_models.append(model)
            return self.client.chat

    @property
    def chats(self):
        return self.Chats(self)


def _stub_client(monkeypatch):
    client = FakeClient()

    def create_client(*, api_key):
        assert api_key == "test-key"
        return client

    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    return client


def test_interactive_questions_reuse_chat_and_keep_history(monkeypatch, capsys):
    client = _stub_client(monkeypatch)
    answers = iter(["その違いは？", ""])

    def get_next_question(prompt):
        assert "終了するには空行" in prompt
        return next(answers)

    monkeypatch.setattr(builtins, "input", get_next_question)
    monkeypatch.setattr(
        sys,
        "argv",
        ["app.ask", "--interactive", "LoRAとは何ですか？"],
    )

    ask_module.main()

    assert client.created_models == [ask_module.MODEL]
    assert client.chat.questions == ["LoRAとは何ですか？", "その違いは？"]
    output = capsys.readouterr().out
    assert "回答: LoRAとは何ですか？" in output
    assert "回答: その違いは？" in output
    assert output.count("[トークン数]") == 2


def test_interactive_mode_can_start_without_an_initial_question(monkeypatch):
    client = _stub_client(monkeypatch)
    answers = iter(["最初の質問", ""])

    def get_next_question(prompt):
        assert "終了するには空行" in prompt
        return next(answers)

    monkeypatch.setattr(builtins, "input", get_next_question)
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive"])

    ask_module.main()

    assert client.chat.questions == ["最初の質問"]


def test_default_question_remains_one_shot(monkeypatch):
    client = _stub_client(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["app.ask"])

    ask_module.main()

    assert client.chat.questions == [ask_module.DEFAULT_QUESTION]
