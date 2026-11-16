from types import SimpleNamespace

import app.ask as ask_module


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return SimpleNamespace(text=f"answer to {question}", usage_metadata=None)


def test_main_keeps_chat_history_for_follow_up_questions(monkeypatch, capsys):
    chat = FakeChat()
    created_models = []

    def create_chat(*, model):
        created_models.append(model)
        return chat

    client = SimpleNamespace(chats=SimpleNamespace(create=create_chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    questions = iter(["続けて質問", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.main()

    assert chat.questions == ["最初の質問", "続けて質問"]
    assert created_models == [ask_module.MODEL]
    assert "answer to 続けて質問" in capsys.readouterr().out
