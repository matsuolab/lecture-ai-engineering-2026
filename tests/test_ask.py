from types import SimpleNamespace

from app import ask as ask_module


def test_main_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=5),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["ask", "質問"])

    ask_module.main()

    output = capsys.readouterr().out
    assert "回答" in output
    assert "[入力トークン数] 12" in output
    assert "[出力トークン数] 5" in output