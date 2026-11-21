from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
        text="answer",
    )

    class FakeModels:
        def generate_content(self, model, contents):
            return response

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    output = capsys.readouterr().out
    assert "入力: 12" in output
    assert "出力: 7" in output


def test_interactive_chat_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []

    class FakeChat:
        def send_message(self, message):
            sent_messages.append(message)
            return SimpleNamespace(
                usage_metadata=None,
                text=f"answer to {message}",
            )

    fake_chat = FakeChat()

    class FakeChats:
        def create(self, model):
            assert model == ask_module.MODEL
            return fake_chat

    class FakeClient:
        chats = FakeChats()

    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    answers = iter(["follow-up question", "/exit"])
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: next(answers),
    )

    ask_module.interactive_chat("first question")
    output = capsys.readouterr().out

    assert sent_messages == ["first question", "follow-up question"]
    assert output.count("answer to") == 2