from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
    )

    class FakeChat:
        def send_message(self, question):
            return response

    chat = FakeChat()
    assert ask.ask("question", chat) == "answer"
    assert capsys.readouterr().out == "[usage] input=12 tokens, output=34 tokens\n"


def test_ask_sends_follow_up_to_same_chat(capsys):
    questions = []

    class FakeChat:
        def send_message(self, question):
            questions.append(question)
            return SimpleNamespace(
                text=f"answer to {question}",
                usage_metadata=SimpleNamespace(prompt_token_count=1, candidates_token_count=2),
            )

    chat = FakeChat()
    assert ask.ask("first question", chat) == "answer to first question"
    assert ask.ask("follow-up", chat) == "answer to follow-up"
    assert questions == ["first question", "follow-up"]
    capsys.readouterr()


def test_create_chat_keeps_owning_client_alive(monkeypatch):
    class FakeChats:
        def create(self, **kwargs):
            return object()

    class FakeClient:
        def __init__(self, api_key):
            self.chats = FakeChats()

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    session = ask.create_chat()

    assert isinstance(session._client, FakeClient)