import sys
import weakref

from app import ask


class FakeResponse:
    text = "回答"
    usage_metadata = None


class FakeChat:
    def __init__(self):
        self.history = []
        self.model = None
        self.client_ref = None

    def send_message(self, question):
        assert self.client_ref is not None and self.client_ref() is not None
        self.history.append(question)
        return FakeResponse()


class FakeChats:
    def __init__(self, chat):
        self.chat = chat

    def create(self, *, model):
        self.chat.model = model
        return self.chat


class FakeClient:
    def __init__(self, chat):
        self.chats = FakeChats(chat)
        chat.client_ref = weakref.ref(self)


def test_interactive_mode_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    chat = FakeChat()
    monkeypatch.setattr(ask.genai, "Client", lambda **_: FakeClient(chat))
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive"])
    questions = iter(["最初の質問", "続けて質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask.main()

    assert chat.model == ask.MODEL
    assert chat.history == ["最初の質問", "続けて質問"]
    assert "回答" in capsys.readouterr().out


def test_interactive_mode_sends_initial_question_before_follow_ups(monkeypatch):
    chat = FakeChat()
    monkeypatch.setattr(ask.genai, "Client", lambda **_: FakeClient(chat))
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive", "最初の質問"])
    questions = iter(["続けて質問", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask.main()

    assert chat.history == ["最初の質問", "続けて質問"]
