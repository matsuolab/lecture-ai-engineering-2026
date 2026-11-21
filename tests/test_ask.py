import sys
from types import SimpleNamespace

from app import ask as ask_module


def test_main_reuses_chat_history_for_follow_up_questions(monkeypatch, capsys):
    questions = []

    class FakeChat:
        def send_message(self, question):
            questions.append(question)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=5,
                ),
                text=f"answer to {question}",
            )

    chat = FakeChat()
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "first question"])
    prompts = iter(["follow-up question", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(prompts))

    ask_module.main()

    output = capsys.readouterr().out
    assert questions == ["first question", "follow-up question"]
    assert output.count("[トークン数]") == 2
    assert "answer to first question" in output
    assert "answer to follow-up question" in output