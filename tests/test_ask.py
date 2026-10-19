from types import SimpleNamespace

from app import ask as ask_module


def test_ask_reports_response_time_and_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答です",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=5,
        ),
    )

    class FakeModels:
        def generate_content(self, *, model, contents):
            assert model == ask_module.MODEL
            assert contents == "質問です"
            return response

    class FakeClient:
        models = FakeModels()

    def create_client(**kwargs):
        assert kwargs == {"api_key": "test-key"}
        return FakeClient()

    clock_values = iter([1.0, 3.5])
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(clock_values))

    assert ask_module.ask("質問です") == "回答です"

    output = capsys.readouterr().out
    assert "[応答時間] 2.50秒" in output
    assert "[トークン数] 入力: 12, 出力: 5" in output
