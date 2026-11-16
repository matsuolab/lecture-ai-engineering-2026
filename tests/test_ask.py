from types import SimpleNamespace

from app import ask


def test_ask_sends_message_to_chat_and_prints_token_usage(capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
        text="回答",
    )

    class FakeChat:
        def send_message(self, question):
            assert question == "質問"
            return response

    assert ask.ask(FakeChat(), "質問") == "回答"
    assert capsys.readouterr().out.strip() == "[トークン] 入力: 12, 出力: 34"


def test_main_keeps_follow_up_questions_in_same_chat(monkeypatch, capsys):
    sent_questions = []

    class FakeChat:
        def send_message(self, question):
            sent_questions.append(question)
            return SimpleNamespace(
                usage_metadata=None,
                text=f"{question}への回答",
            )

    class FakeChats:
        def create(self, *, model):
            return chat

    class FakeClient:
        chats = FakeChats()

        def __init__(self, *, api_key):
            pass

    chat = FakeChat()
    prompts = iter(["2つ目の質問", ""])
    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])

    ask.main()

    assert sent_questions == ["最初の質問", "2つ目の質問"]
    assert "2つ目の質問への回答" in capsys.readouterr().out