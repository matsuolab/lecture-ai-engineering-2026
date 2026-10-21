from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_token_usage_and_returns_response(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
        text="回答です",
    )
    sent_messages = []
    chat = SimpleNamespace(
        send_message=lambda message: sent_messages.append(message) or response
    )

    result = ask_module.ask("質問", chat)

    assert result == "回答です"
    assert sent_messages == ["質問"]
    assert capsys.readouterr().out == "[トークン数] 入力: 12, 出力: 7\n"


def test_main_reuses_chat_for_follow_up_questions(monkeypatch):
    import sys

    sent_messages = []
    response = SimpleNamespace(usage_metadata=None, text="回答です")
    chat = SimpleNamespace(
        send_message=lambda message: sent_messages.append(message) or response
    )
    created_chats = []

    def create_chat(**kwargs):
        created_chats.append(kwargs)
        return chat

    client = SimpleNamespace(chats=SimpleNamespace(create=create_chat))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(sys, "argv", ["app.ask", "最初の質問"])
    monkeypatch.setattr("builtins.input", lambda prompt: "続きの質問" if len(sent_messages) == 1 else "")

    ask_module.main()

    assert sent_messages == ["最初の質問", "続きの質問"]
    assert created_chats == [{"model": ask_module.MODEL}]