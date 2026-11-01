from types import SimpleNamespace
import sys
import weakref

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    class FakeChat:
        def send_message(self, message):
            return SimpleNamespace(
                text="answer",
                usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=4),
            )

    class FakeChats:
        def create(self, **kwargs):
            return FakeChat()

    class FakeClient:
        def __init__(self, *, api_key):
            self.chats = FakeChats()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out == "[tokens] 入力: 12, 出力: 4\n"


def test_interactive_mode_reuses_chat_history(monkeypatch, capsys):
    class FakeChat:
        def __init__(self, client_reference):
            self.client_reference = client_reference
            self.messages = []

        def send_message(self, message):
            assert self.client_reference() is not None
            self.messages.append(message)
            return SimpleNamespace(
                text=f"answer to {message}",
                usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=4),
            )

    class FakeChats:
        def __init__(self, client):
            self.client_reference = weakref.ref(client)

        def create(self, **kwargs):
            return FakeChat(self.client_reference)

    class FakeClient:
        def __init__(self, *, api_key):
            self.chats = FakeChats(self)

    chat = None
    original_create = FakeChats.create

    def create_chat(chats, **kwargs):
        nonlocal chat
        chat = original_create(chats, **kwargs)
        return chat

    monkeypatch.setattr(FakeChats, "create", create_chat)

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive", "first question"])
    questions = iter(["follow-up", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.main()

    assert chat.messages == ["first question", "follow-up"]
    assert "answer to follow-up" in capsys.readouterr().out