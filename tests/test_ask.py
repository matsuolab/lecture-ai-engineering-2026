import sys
from types import SimpleNamespace

from app import ask as ask_module
from app.config import MODEL


def test_main_keeps_chat_history_for_follow_up_questions(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(
                text=f"answer: {question}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3,
                    candidates_token_count=5,
                ),
            )

    chat = FakeChat()
    fake_client = SimpleNamespace(
        chats=SimpleNamespace(
            create=lambda *, model: chat if model == MODEL else None,
        ),
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda *, api_key: fake_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "first question"])
    questions = iter(["follow-up question", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.main()

    output = capsys.readouterr().out
    assert chat.questions == ["first question", "follow-up question"]
    assert "answer: first question" in output
    assert "answer: follow-up question" in output
    assert output.count("input tokens: 3, output tokens: 5") == 2
