from types import SimpleNamespace
import sys

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
        text="answer",
    )
    chat = SimpleNamespace(send_message=lambda question: response)

    result = ask_module.ask("question", chat)

    assert result == "answer"
    assert capsys.readouterr().out == "[tokens] input=12 output=7\n"


def test_main_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    messages = []
    response = SimpleNamespace(
        usage_metadata=None,
        text="answer",
    )

    def send_message(question):
        messages.append(question)
        return response

    chat = SimpleNamespace(send_message=send_message)
    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: chat),
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "first question"])
    questions = iter(["follow-up", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.main()

    assert messages == ["first question", "follow-up"]
    assert capsys.readouterr().out.count("answer") == 2