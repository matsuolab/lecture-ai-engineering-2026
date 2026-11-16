from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
        text="回答",
    )

    class FakeClient:
        def __init__(self, api_key):
            self.models = SimpleNamespace(generate_content=lambda **kwargs: response)

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("質問") == "回答"
    assert capsys.readouterr().out.strip() == "[トークン] 入力: 12 / 出力: 7"


def test_ask_handles_missing_usage_metadata(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="回答")

    class FakeClient:
        def __init__(self, api_key):
            self.models = SimpleNamespace(generate_content=lambda **kwargs: response)

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("質問") == "回答"
    assert capsys.readouterr().out.strip() == "[トークン] 入力: 不明 / 出力: 不明"