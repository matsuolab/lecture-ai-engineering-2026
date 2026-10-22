from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
        text="回答",
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **_: response)
    )
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask.genai, "Client", lambda **_: client)

    assert ask.ask("質問") == "回答"
    assert "[tokens] 入力: 12, 出力: 34" in capsys.readouterr().out