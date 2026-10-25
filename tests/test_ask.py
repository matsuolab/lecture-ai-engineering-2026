from types import SimpleNamespace

import pytest

from app import ask


@pytest.mark.parametrize(
    ("usage_metadata", "expected"),
    [
        (
            SimpleNamespace(prompt_token_count=12, candidates_token_count=5),
            "[トークン数] 入力: 12 / 出力: 5",
        ),
        (None, "[トークン数] 入力: 不明 / 出力: 不明"),
        (
            SimpleNamespace(prompt_token_count=None, candidates_token_count=5),
            "[トークン数] 入力: 不明 / 出力: 5",
        ),
    ],
)
def test_ask_prints_token_counts(monkeypatch, capsys, usage_metadata, expected):
    response = SimpleNamespace(text="answer", usage_metadata=usage_metadata)
    chat = SimpleNamespace(send_message=lambda question: response)

    assert ask.ask(chat, "question") == "answer"
    assert expected in capsys.readouterr().out


def test_ask_prints_response_time(monkeypatch, capsys):
    response = SimpleNamespace(text="answer", usage_metadata=None)
    chat = SimpleNamespace(send_message=lambda question: response)
    clock = iter([10.0, 11.234])
    monkeypatch.setattr(ask.time, "perf_counter", lambda: next(clock))

    assert ask.ask(chat, "question") == "answer"
    assert "[応答時間] 1.23秒" in capsys.readouterr().out


def test_create_chat_passes_temperature_in_generate_content_config():
    call = {}

    def create(**kwargs):
        call.update(kwargs)
        return "chat"

    client = SimpleNamespace(chats=SimpleNamespace(create=create))

    assert ask.create_chat(client, temperature=0.2) == "chat"
    assert call["model"] == ask.MODEL
    assert call["config"].temperature == 0.2


def test_main_keeps_chat_history_across_questions(monkeypatch, capsys):
    questions = iter(["follow-up", ""])
    sent_questions = []
    response = SimpleNamespace(text="answer", usage_metadata=None)
    client_closed = False

    class Chat:
        def send_message(self, question):
            assert not client_closed
            sent_questions.append(question)
            return response

    class Client:
        chats = SimpleNamespace(create=lambda **kwargs: chat)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            nonlocal client_closed
            client_closed = True

    chat = Chat()
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: Client())
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))
    monkeypatch.setattr("sys.argv", ["ask.py", "first question"])

    ask.main()

    assert sent_questions == ["first question", "follow-up"]
    assert client_closed
    output = capsys.readouterr().out
    assert output.count("answer") == 2
