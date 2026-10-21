from types import SimpleNamespace

import app.ask as ask_module


def test_chat_reuses_conversation_for_each_question(monkeypatch, capsys):
    sent_messages = []
    conversation = SimpleNamespace(
        send_message=lambda question: sent_messages.append(question)
        or SimpleNamespace(
            text=f"回答: {question}",
            usage_metadata=SimpleNamespace(prompt_token_count=2, candidates_token_count=3),
        )
    )
    chats = SimpleNamespace(create=lambda model: conversation)
    client = SimpleNamespace(chats=chats)
    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    questions = iter(["一問目", "二問目", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.chat()

    output = capsys.readouterr().out
    assert sent_messages == ["一問目", "二問目"]
    assert "回答: 一問目" in output
    assert "回答: 二問目" in output
    assert output.count("入力: 2 tokens, 出力: 3 tokens") == 2