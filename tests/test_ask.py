from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
    )

    class FakeChat:
        def send_message(self, question):
            return response

    class FakeChats:
        def create(self, **kwargs):
            return FakeChat()

    class FakeClient:
        chats = FakeChats()

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: FakeClient())

    assert ask_module.ask("質問") == "回答"
    assert "[トークン] 入力: 12 / 出力: 7" in capsys.readouterr().out


def test_main_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_questions = []
    created_chats = []

    class FakeChat:
        def send_message(self, question):
            sent_questions.append(question)
            return SimpleNamespace(text=f"{question}への回答", usage_metadata=None)

    class FakeChats:
        def create(self, **kwargs):
            chat = FakeChat()
            created_chats.append(chat)
            return chat

    class FakeClient:
        chats = FakeChats()

    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    inputs = iter(["続きの質問", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    ask_module.main()

    assert sent_questions == ["最初の質問", "続きの質問"]
    assert len(created_chats) == 1
    assert "続きの質問への回答" in capsys.readouterr().out