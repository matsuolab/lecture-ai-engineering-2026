import weakref
from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
    )
    chat = SimpleNamespace(send_message=lambda _: response)
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **_: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out == "[トークン数] 入力: 12 / 出力: 34\n"


def test_ask_reports_unavailable_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(text="answer", usage_metadata=None)
    chat = SimpleNamespace(send_message=lambda _: response)
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **_: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out == "[トークン数] 入力: 不明 / 出力: 不明\n"


def test_ask_keeps_client_alive_while_sending_message(monkeypatch):
    response = SimpleNamespace(text="answer", usage_metadata=None)

    class FakeChat:
        def __init__(self, client_ref):
            self.client_ref = client_ref

        def send_message(self, _):
            if self.client_ref() is None:
                raise RuntimeError("client was closed")
            return response

    class FakeClient:
        def __init__(self, **_):
            self.chats = SimpleNamespace(
                create=lambda **_: FakeChat(weakref.ref(self))
            )

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"


def test_chat_mode_keeps_using_the_same_chat_for_follow_up_questions(
    monkeypatch, capsys
):
    sent_messages = []
    responses = iter(
        [
            SimpleNamespace(text="first answer", usage_metadata=None),
            SimpleNamespace(text="follow-up answer", usage_metadata=None),
        ]
    )
    chat = SimpleNamespace(
        send_message=lambda message: (
            sent_messages.append(message) or next(responses)
        )
    )
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **_: chat))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    questions = iter(["follow-up", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))
    monkeypatch.setattr("sys.argv", ["app.ask", "--chat", "first question"])

    ask_module.main()

    assert sent_messages == ["first question", "follow-up"]
    assert capsys.readouterr().out.count("[トークン数]") == 2
