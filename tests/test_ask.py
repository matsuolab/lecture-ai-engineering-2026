from types import SimpleNamespace

from app import ask as ask_module


def test_ask_sends_message_to_chat_and_displays_usage(capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
        text="回答",
    )
    sent_messages = []
    chat = SimpleNamespace(
        send_message=lambda message: sent_messages.append(message) or response
    )

    assert ask_module.ask("質問", chat) == "回答"

    assert sent_messages == ["質問"]
    assert "[トークン数] 入力: 12 / 出力: 34" in capsys.readouterr().out


def test_run_chat_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []

    def send_message(message):
        sent_messages.append(message)
        return SimpleNamespace(usage_metadata=None, text=f"回答{len(sent_messages)}")

    chat = SimpleNamespace(send_message=send_message)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(
            chats=SimpleNamespace(create=lambda **kwargs: chat)
        ),
    )
    questions = iter(["最初の質問", "続きの質問", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.run_chat()

    assert sent_messages == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "回答1" in output
    assert "回答2" in output


def test_ask_displays_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
        text="回答",
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **kwargs: response)
        ),
    )

    assert ask_module.ask("質問") == "回答"

    assert "[トークン数] 入力: 12 / 出力: 34" in capsys.readouterr().out
