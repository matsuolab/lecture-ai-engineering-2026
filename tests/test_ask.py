from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=8),
        text="回答",
    )

    class FakeModels:
        def generate_content(self, *, model, contents):
            return response

    class FakeClient:
        def __init__(self, *, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("質問") == "回答"
    assert capsys.readouterr().out == "[トークン] 入力: 12, 出力: 8\n"


def test_chat_keeps_using_the_same_conversation(monkeypatch, capsys):
    sent_questions = []
    responses = iter(
        [
            SimpleNamespace(
                usage_metadata=SimpleNamespace(prompt_token_count=5, candidates_token_count=3),
                text="1つ目の回答",
            ),
            SimpleNamespace(
                usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=4),
                text="2つ目の回答",
            ),
        ]
    )

    class FakeConversation:
        def send_message(self, question):
            sent_questions.append(question)
            return next(responses)

    class FakeChats:
        def create(self, *, model):
            return FakeConversation()

    class FakeClient:
        def __init__(self, *, api_key):
            self.chats = FakeChats()

    answers = iter(["最初の質問", "続きの質問", "exit"])
    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    ask.chat()

    assert sent_questions == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "1つ目の回答" in output
    assert "2つ目の回答" in output