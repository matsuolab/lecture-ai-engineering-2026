from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    fake_usage = SimpleNamespace(prompt_token_count=123, response_token_count=45)
    fake_response = SimpleNamespace(text="テスト回答", usage_metadata=fake_usage)

    class FakeModels:
        def generate_content(self, model, contents):
            assert model == ask_module.MODEL
            assert contents == "Q"
            return fake_response

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "dummy-key")
    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: FakeClient(api_key))

    result = ask_module.ask("Q")

    assert result == "テスト回答"
    captured = capsys.readouterr()
    assert "入力トークン数: 123" in captured.out
    assert "出力トークン数: 45" in captured.out
