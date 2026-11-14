from types import SimpleNamespace

from app import ask


def test_interactive_chat_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    questions = []

    class FakeChat:
        def send_message(self, question):
            questions.append(question)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(prompt_token_count=2, candidates_token_count=3),
                text=f"回答: {question}",
            )

    chat = FakeChat()
    clients = []

    class FakeClient:
        def __init__(self, api_key):
            self.chats = SimpleNamespace(create=self.create_chat)
            clients.append(api_key)

        def create_chat(self, model):
            return chat

    prompts = iter(["最初の質問", "続けて質問", ":q"])
    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))

    ask.interactive_chat()

    assert questions == ["最初の質問", "続けて質問"]
    assert clients == ["test-key"]
    assert "回答: 続けて質問" in capsys.readouterr().out
