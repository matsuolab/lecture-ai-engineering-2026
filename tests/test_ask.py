from types import SimpleNamespace

from app import ask as ask_module


def test_main_keeps_chat_history_for_follow_up_questions(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=1, candidates_token_count=1
                ),
                text=f"answer: {question}",
            )

    chat = FakeChat()

    class FakeClient:
        def __init__(self, api_key):
            self.chats = SimpleNamespace(create=self.create_chat)

        def create_chat(self, model):
            assert model == ask_module.MODEL
            return chat

    questions = iter(["second question", ""])
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "first question"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(questions))

    ask_module.main()

    assert chat.questions == ["first question", "second question"]
    assert "answer: first question" in capsys.readouterr().out