"""質問スクリプトのテスト（LLMもAPIキーも使わない）。"""

from types import SimpleNamespace

from app import ask as ask_module


def test_chat_keeps_conversation_history(monkeypatch, capsys):
    sent_messages = []

    class FakeChat:
        def send_message(self, question):
            sent_messages.append(question)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3,
                    candidates_token_count=4,
                ),
                text=f"回答: {question}",
            )

    class FakeChats:
        def create(self, *, model):
            assert model == ask_module.MODEL
            return FakeChat()

    class FakeClient:
        chats = FakeChats()

        def __init__(self, *, api_key):
            assert api_key == "test-key"

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        "sys.argv", ["app.ask", "--chat"]
    )
    questions = iter(["最初の質問", "続けて質問", "終了"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(questions))

    ask_module.main()

    output = capsys.readouterr().out
    assert sent_messages == ["最初の質問", "続けて質問"]
    assert output.count("[トークン数]") == 2
    assert "回答: 最初の質問" in output
    assert "回答: 続けて質問" in output
