from types import SimpleNamespace

import pytest

from app import ask


def _response(text="回答", input_tokens=12, output_tokens=34):
    return SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=input_tokens,
            candidates_token_count=output_tokens,
        ),
        text=text,
    )


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = _response()
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: response,
        )
    )
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("質問") == "回答"
    assert "[usage] input_tokens=12 output_tokens=34" in capsys.readouterr().out


def test_ask_reports_when_usage_metadata_is_unavailable(monkeypatch, capsys):
    response = _response()
    response.usage_metadata = None
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: response,
        )
    )
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("質問") == "回答"
    assert "[usage] unavailable" in capsys.readouterr().out


def test_chat_sends_multiple_questions_to_the_same_chat(monkeypatch, capsys):
    calls = []
    chat = SimpleNamespace(
        send_message=lambda question: calls.append(question)
        or _response(f"{question}への回答")
    )
    create_calls = []
    client = SimpleNamespace(
        chats=SimpleNamespace(
            create=lambda **kwargs: create_calls.append(kwargs) or chat,
        )
    )
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    questions = iter(["最初の質問", "続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask.chat()

    assert create_calls == [{"model": ask.MODEL}]
    assert calls == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "最初の質問への回答" in output
    assert "続きの質問への回答" in output
    assert output.count("[usage] input_tokens=12 output_tokens=34") == 2


@pytest.mark.parametrize("exit_command", ["exit", "終了"])
def test_chat_exits_on_exit_command(monkeypatch, capsys, exit_command):
    sends = []
    chat = SimpleNamespace(send_message=lambda question: sends.append(question))
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: exit_command)

    ask.chat()

    assert sends == []
    capsys.readouterr()


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt])
def test_chat_exits_safely_when_input_is_interrupted(monkeypatch, capsys, exception):
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: None))
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    def interrupt(_prompt):
        raise exception

    monkeypatch.setattr("builtins.input", interrupt)

    ask.chat()

    capsys.readouterr()


def test_chat_handles_keyboard_interrupt_during_message_send(monkeypatch, capsys):
    chat = SimpleNamespace(
        send_message=lambda question: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: "質問")

    ask.chat()

    capsys.readouterr()


def test_chat_api_error_uses_existing_error_handler(monkeypatch, capsys):
    def fail_to_send(_question):
        raise ask.errors.APIError(
            429,
            {"error": {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}},
        )

    chat = SimpleNamespace(send_message=fail_to_send)
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: "質問")
    monkeypatch.setattr("sys.argv", ["app.ask", "--chat"])

    with pytest.raises(SystemExit) as error:
        ask.main()

    assert error.value.code == 1
    assert "レート制限に達しました" in capsys.readouterr().out


def test_main_keeps_single_question_mode(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(ask, "ask", lambda question: calls.append(question) or "回答")
    monkeypatch.setattr("sys.argv", ["app.ask", "指定した質問"])

    ask.main()

    assert calls == ["指定した質問"]
    output = capsys.readouterr().out
    assert "[質問] 指定した質問" in output
    assert "回答" in output
