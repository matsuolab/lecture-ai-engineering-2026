"""質問スクリプトのテスト（LLMもAPIキーも使わない）。"""

from types import SimpleNamespace

from app import ask as ask_module


def test_run_chat_keeps_history_between_questions(monkeypatch, capsys):
    sent_messages = []
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
    )
    chat = SimpleNamespace(
        send_message=lambda question: sent_messages.append(question) or response
    )
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    questions = iter(["最初の質問", "続けて聞きたい質問", "終了"])

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.run_chat()

    assert sent_messages == ["最初の質問", "続けて聞きたい質問"]
    output = capsys.readouterr().out
    assert output.count("入力: 12") == 2
    assert output.count("回答") == 2
