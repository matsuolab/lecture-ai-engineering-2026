from types import SimpleNamespace

import app.ask


def test_ask_prints_input_and_output_tokens(monkeypatch, capsys):
    response = SimpleNamespace(
        text="こんにちは",
        usage_metadata=SimpleNamespace(
            prompt_token_count=123,
            candidates_token_count=45,
        ),
    )

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key

        class models:
            @staticmethod
            def generate_content(model, contents):
                assert model == app.ask.MODEL
                assert contents == "質問"
                return response

    monkeypatch.setattr(app.ask, "get_api_key", lambda: "fake-key")
    monkeypatch.setattr(app.ask.genai, "Client", lambda api_key: FakeClient(api_key))

    result = app.ask.ask("質問")
    captured = capsys.readouterr()

    assert result == "こんにちは"
    assert "入力トークン数" in captured.out
    assert "出力トークン数" in captured.out
    assert "123" in captured.out
    assert "45" in captured.out
