from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
        text="回答",
    )

    class FakeChat:
        def send_message(self, question):
            return response

    class FakeChats:
        def create(self, **kwargs):
            return FakeChat()

    class FakeClient:
        def __init__(self, api_key):
            self.chats = FakeChats()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out == "[トークン] 入力: 12 / 出力: 34\n"


def test_ask_reports_unknown_counts_when_usage_metadata_is_missing(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="回答")

    class FakeChat:
        def send_message(self, question):
            return response

    class FakeChats:
        def create(self, **kwargs):
            return FakeChat()

    class FakeClient:
        def __init__(self, api_key):
            self.chats = FakeChats()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out == "[トークン] 入力: 不明 / 出力: 不明\n"


def test_main_keeps_one_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_questions = []
    client_state = {"closed": False}

    class FakeChat:
        def send_message(self, question):
            assert not client_state["closed"]
            sent_questions.append(question)
            return SimpleNamespace(
                usage_metadata=None,
                text=f"{question}への回答",
            )

    class FakeChats:
        def __init__(self):
            self.chat = FakeChat()
            self.created = 0

        def create(self, **kwargs):
            self.created += 1
            return self.chat

    chats = FakeChats()

    class FakeClient:
        def __init__(self, api_key):
            self.chats = chats

        def __del__(self):
            client_state["closed"] = True

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module, "DEFAULT_QUESTION", "最初の質問")
    monkeypatch.setattr("sys.argv", ["app.ask"])
    questions = iter(["続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.main()

    assert chats.created == 1
    assert sent_questions == ["最初の質問", "続きの質問"]
    assert "続きの質問への回答" in capsys.readouterr().out