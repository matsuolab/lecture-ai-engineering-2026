from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
        text="回答",
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)

    assert ask.ask("質問") == "回答"
    assert "[トークン数] 入力: 12, 出力: 7" in capsys.readouterr().out


def test_interactive_chat_sends_followups_to_the_same_chat(monkeypatch, capsys):
    responses = iter(
        [
            SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=12, candidates_token_count=7
                ),
                text="最初の回答",
            ),
            SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=20, candidates_token_count=8
                ),
                text="続きの回答",
            ),
        ]
    )
    sent_messages = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return next(responses)

    chat = FakeChat()
    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: chat)
    )
    questions = iter(["最初の質問", "続けて質問", "/exit"])
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(questions))

    ask.interactive_chat()

    assert sent_messages == ["最初の質問", "続けて質問"]
    output = capsys.readouterr().out
    assert "最初の回答" in output
    assert "続きの回答" in output
    assert output.count("[トークン数]") == 2


def test_interactive_chat_sends_initial_question_before_followups(monkeypatch):
    sent_messages = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(usage_metadata=None, text="回答")

    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: FakeChat())
    )
    questions = iter(["追加質問", "/exit"])
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(questions))

    ask.interactive_chat("最初の質問")

    assert sent_messages == ["最初の質問", "追加質問"]