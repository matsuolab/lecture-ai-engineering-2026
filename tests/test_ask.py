from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_token_usage_and_returns_text(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
        text="回答",
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    result = ask_module.ask("質問")
    output = capsys.readouterr().out

    assert result == "回答"
    assert "入力: 12" in output
    assert "出力: 7" in output