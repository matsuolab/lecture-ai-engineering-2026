from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_usage_metadata(monkeypatch, capsys):
    fake_response = SimpleNamespace(
        text="回答です",
        usage_metadata=SimpleNamespace(prompt_token_count=123, response_token_count=45),
    )

    class FakeModels:
        def generate_content(self, model, contents):
            assert model == ask_module.MODEL
            assert contents == "質問"
            return fake_response

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()

    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: FakeClient(api_key))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "fake-key")

    result = ask_module.ask("質問")

    assert result == "回答です"
    printed = capsys.readouterr().out
    assert "入力トークン数: 123" in printed
    assert "出力トークン数: 45" in printed
