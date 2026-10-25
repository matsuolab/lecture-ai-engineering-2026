from types import SimpleNamespace

import app.ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="回答",
    )

    class FakeModels:
        def generate_content(self, *, model, contents):
            assert model == ask_module.MODEL
            assert contents == "質問"
            return response

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-api-key"
            self.models = FakeModels()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-api-key")

    assert ask_module.ask("質問") == "回答"
    assert "[token] 入力: 12, 出力: 34" in capsys.readouterr().out


def test_ask_reports_missing_token_usage(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="回答")

    class FakeModels:
        def generate_content(self, *, model, contents):
            assert model == ask_module.MODEL
            assert contents == "質問"
            return response

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "test-api-key"
            self.models = FakeModels()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-api-key")

    assert ask_module.ask("質問") == "回答"
    assert "[token] 使用量情報なし" in capsys.readouterr().out
