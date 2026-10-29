from types import SimpleNamespace

from app import ask


def test_run_conversation_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []
    created_chats = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(
                text=f"回答: {message}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3,
                    candidates_token_count=2,
                ),
            )

    fake_chat = FakeChat()

    class FakeChats:
        def create(self, *, model):
            created_chats.append(model)
            return fake_chat

    monkeypatch.setattr(
        ask.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(chats=FakeChats()),
    )
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    questions = iter(["私の名前は何ですか？", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(questions))

    ask.run_conversation("私の名前は太郎です。")

    assert sent_messages == ["私の名前は太郎です。", "私の名前は何ですか？"]
    assert created_chats == [ask.MODEL]
    assert "入力: 3, 出力: 2" in capsys.readouterr().out
