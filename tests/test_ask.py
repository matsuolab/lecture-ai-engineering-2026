from types import SimpleNamespace

from app import ask as ask_module


def _mock_client(monkeypatch, response):
    chat = SimpleNamespace(send_message=lambda question: response)
    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: chat)
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    return chat


def test_ask_prints_token_usage(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12, candidates_token_count=7
        ),
        text="answer",
    )
    chat = _mock_client(monkeypatch, response)

    assert ask_module.ask(chat, "question") == "answer"
    assert "[usage] input_tokens=12 output_tokens=7" in capsys.readouterr().out


def test_ask_handles_missing_usage_and_text(monkeypatch, capsys):
    chat = _mock_client(monkeypatch, SimpleNamespace(usage_metadata=None, text=None))

    assert ask_module.ask(chat, "question") == "モデルからテキスト応答がありませんでした。"
    assert "[usage] 利用不可" in capsys.readouterr().out


def test_main_sends_follow_up_questions_to_same_chat(monkeypatch):
    sent_questions = []
    chat = SimpleNamespace(
        send_message=lambda question: (
            sent_questions.append(question),
            SimpleNamespace(usage_metadata=None, text=f"answer: {question}"),
        )[1]
    )
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    follow_ups = iter(["続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(follow_ups))

    ask_module.main()

    assert sent_questions == ["最初の質問", "続きの質問"]