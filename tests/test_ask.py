from app import ask as ask_module


class FakeUsageMetadata:
    prompt_token_count = 123
    candidates_token_count = 45


class FakeResponse:
    text = "これはテストです。"
    usage_metadata = FakeUsageMetadata()


class FakeModels:
    def generate_content(self, model, contents):
        assert model == ask_module.MODEL
        assert contents == "テスト質問"
        return FakeResponse()


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = FakeModels()


def test_ask_prints_input_and_output_tokens(monkeypatch, capsys):
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)

    result = ask_module.ask("テスト質問")

    assert result == "これはテストです。"
    out = capsys.readouterr().out
    assert "[入力トークン] 123" in out
    assert "[出力トークン] 45" in out
