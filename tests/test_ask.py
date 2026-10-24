from types import SimpleNamespace

from app import ask as ask_module


class FakeChat:
    def __init__(self, response):
        self.response = response
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return self.response


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
    )

    assert ask_module.ask(FakeChat(response), "質問") == "回答"
    output = capsys.readouterr().out
    assert "入力トークン数: 12" in output
    assert "出力トークン数: 7" in output


def test_ask_returns_answer_when_usage_counts_are_missing():
    response = SimpleNamespace(text="回答", usage_metadata=SimpleNamespace())

    assert ask_module.ask(FakeChat(response), "質問") == "回答"


def test_main_reuses_chat_for_follow_up_questions(monkeypatch):
    response = SimpleNamespace(text="回答", usage_metadata=None)
    chat = FakeChat(response)
    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: chat)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])
    questions = iter(["続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.main()

    assert chat.questions == ["最初の質問", "続きの質問"]