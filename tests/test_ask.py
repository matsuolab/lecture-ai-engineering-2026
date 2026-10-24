from types import SimpleNamespace

from app import ask as ask_module


def test_main_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    sent_messages = []

    class FakeChat:
        def send_message(self, question):
            sent_messages.append(question)
            return SimpleNamespace(
                text=f"回答: {question}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=1,
                    candidates_token_count=2,
                ),
            )

    class FakeChats:
        def __init__(self):
            self.create_calls = []

        def create(self, **kwargs):
            self.create_calls.append(kwargs)
            return FakeChat()

    chats = FakeChats()
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: SimpleNamespace(chats=chats))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "最初の質問"])

    def answer_then_exit(prompt):
        if sent_messages == ["最初の質問"]:
            return "続きの質問"
        return "終了"

    monkeypatch.setattr("builtins.input", answer_then_exit)

    ask_module.main()

    assert sent_messages == ["最初の質問", "続きの質問"]
    assert len(chats.create_calls) == 1
    assert chats.create_calls[0]["model"] == ask_module.MODEL
    assert "回答: 続きの質問" in capsys.readouterr().out
