from types import SimpleNamespace

from app import ask as ask_module


def test_ask_displays_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="回答",
    )

    class FakeModels:
        def generate_content(self, *, model, contents):
            return response

    class FakeClient:
        def __init__(self, *, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out.strip() == "[トークン] 入力: 12 / 出力: 34"


def test_interactive_chat_sends_follow_up_questions_to_same_chat(monkeypatch, capsys):
    sent_questions = []

    class FakeChat:
        def send_message(self, question):
            sent_questions.append(question)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=12,
                    candidates_token_count=34,
                ),
                text=f"{question}への回答",
            )

    class FakeChats:
        def create(self, *, model):
            return chat

    class FakeClient:
        def __init__(self, *, api_key):
            self.chats = FakeChats()

    chat = FakeChat()
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    questions = iter(["追加質問", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.interactive_chat("最初の質問")

    output = capsys.readouterr().out
    assert sent_questions == ["最初の質問", "追加質問"]
    assert "最初の質問への回答" in output
    assert "追加質問への回答" in output
    assert output.count("[トークン] 入力: 12 / 出力: 34") == 2