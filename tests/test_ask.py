from types import SimpleNamespace

from app import ask


def test_chat_keeps_conversation_history(monkeypatch, capsys):
    sent_messages = []
    created_chats = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(
                text=f"reply to {message}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3,
                    candidates_token_count=4,
                ),
            )

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.chats = self

        def create(self, model):
            assert model == ask.MODEL
            conversation = FakeChat()
            created_chats.append(conversation)
            return conversation

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    answers = iter(["それは何に使うの？", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    ask.chat("LoRAとは？")

    output = capsys.readouterr().out
    assert sent_messages == ["LoRAとは？", "それは何に使うの？"]
    assert len(created_chats) == 1
    assert "reply to LoRAとは？" in output
    assert "入力トークン数: 3" in output
    assert "出力トークン数: 4" in output
