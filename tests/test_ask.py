from types import SimpleNamespace
<<<<<<< HEAD
from unittest.mock import patch

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(prompt_token_count=11, response_token_count=7),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )

    with patch("app.ask.get_api_key", return_value="test-key"), patch(
        "app.ask.genai.Client", return_value=client
    ):
        assert ask_module.ask("question") == "answer"

    assert "[tokens] input=11 output=7" in capsys.readouterr().out
=======

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        id="response-1",
        usage=SimpleNamespace(input_tokens=12, output_tokens=34),
        output_text="回答です",
    )

    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs == {"model": ask_module.MODEL, "input": "質問です"}
            return response

    class FakeOpenAI:
        def __init__(self, *, api_key):
            assert api_key == "test-api-key"
            self.responses = FakeResponses()

    monkeypatch.setattr(ask_module, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-api-key")

    assert ask_module.ask("質問です") == "回答です"
    assert capsys.readouterr().out == "[usage] 入力トークン数: 12, 出力トークン数: 34\n"


def test_conversation_sends_previous_response_id(monkeypatch, capsys):
    responses = [
        SimpleNamespace(
            id="response-1",
            usage=SimpleNamespace(input_tokens=12, output_tokens=34),
            output_text="最初の回答",
        ),
        SimpleNamespace(
            id="response-2",
            usage=SimpleNamespace(input_tokens=20, output_tokens=10),
            output_text="続きの回答",
        ),
    ]
    requests = []

    class FakeResponses:
        def create(self, **kwargs):
            requests.append(kwargs)
            return responses[len(requests) - 1]

    class FakeOpenAI:
        def __init__(self, *, api_key):
            assert api_key == "test-api-key"
            self.responses = FakeResponses()

    monkeypatch.setattr(ask_module, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-api-key")
    conversation = ask_module.Conversation()

    assert conversation.ask("最初の質問") == "最初の回答"
    assert conversation.ask("続きの質問") == "続きの回答"

    assert requests == [
        {
            "model": ask_module.MODEL,
            "input": "最初の質問",
        },
        {
            "model": ask_module.MODEL,
            "input": "続きの質問",
            "previous_response_id": "response-1",
        },
    ]
    assert capsys.readouterr().out.count("[usage]") == 2


def test_main_accepts_follow_up_questions_until_blank(monkeypatch, capsys):
    questions = []

    class FakeConversation:
        def ask(self, question):
            questions.append(question)
            return f"{question}への回答"

    monkeypatch.setattr(ask_module, "Conversation", FakeConversation)
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    follow_ups = iter(["続きの質問", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(follow_ups))

    ask_module.main()

    assert questions == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "最初の質問への回答" in output
    assert "続きの質問への回答" in output
>>>>>>> b41fb3571dfdbe52e14fc8a2294579c5529b86bb
