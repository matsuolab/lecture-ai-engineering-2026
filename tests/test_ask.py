from types import SimpleNamespace

from app import ask


def _run_ask(monkeypatch, usage_metadata):
    response = SimpleNamespace(text="answer", usage_metadata=usage_metadata)

    def generate_content(*, model, contents):
        assert model == ask.MODEL
        assert contents == "question"
        return response

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))

    def create_client(*, api_key):
        assert api_key == "test-key"
        return client

    monkeypatch.setattr(ask.genai, "Client", create_client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    return ask.ask("question")


def test_ask_displays_input_and_output_token_counts(monkeypatch, capsys):
    result = _run_ask(
        monkeypatch,
        SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
    )

    assert result == "answer"
    assert (
        "[usage] 入力トークン数: 12, 出力トークン数: 7"
        in capsys.readouterr().out
    )


def test_ask_displays_unknown_counts_when_usage_metadata_is_missing(
    monkeypatch, capsys
):
    _run_ask(monkeypatch, None)

    assert (
        "[usage] 入力トークン数: 不明, 出力トークン数: 不明"
        in capsys.readouterr().out
    )
