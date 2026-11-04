from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_token_usage(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out == "[usage] input_tokens=12 output_tokens=34\n"