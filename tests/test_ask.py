from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(
            prompt_token_count=7,
            candidates_token_count=11,
        ),
    )
    models = SimpleNamespace(generate_content=lambda **kwargs: response)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda api_key: SimpleNamespace(models=models),
    )

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out.strip() == "[tokens] input=7 output=11"