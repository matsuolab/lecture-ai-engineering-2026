from types import SimpleNamespace

from app import ask as ask_module


def test_main_keeps_chat_history_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(
                text=f"回答: {message}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3,
                    candidates_token_count=4,
                ),
            )

    class FakeClient:
        def __init__(self):
            self.chats = SimpleNamespace(create=self.create_chat)

        def create_chat(self, *, model):
            assert model == ask_module.MODEL
            return FakeChat()

    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: FakeClient())
    questions = iter(["それをもう少し詳しく", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])

    ask_module.main()

    output = capsys.readouterr().out
    assert sent_messages == ["最初の質問", "それをもう少し詳しく"]
    assert output.count("[tokens]") == 2
    assert "回答: それをもう少し詳しく" in output
