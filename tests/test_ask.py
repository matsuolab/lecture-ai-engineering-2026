from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
    )
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda api_key: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **kwargs: response)
        ),
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out == "[usage] input_tokens=12, output_tokens=34\n"


def test_ask_reports_unavailable_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(text="回答", usage_metadata=None)
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda api_key: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **kwargs: response)
        ),
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out == "[usage] token counts unavailable\n"
