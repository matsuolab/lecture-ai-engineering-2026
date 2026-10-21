"""素のLLM呼び出しのテスト（実際のAPIは呼ばない）。"""

import app.ask as ask_module


def test_ask_prints_response_time(monkeypatch, capsys):
    class FakeModels:
        def generate_content(self, *, model, contents):
            return type("Response", (), {"text": "answer", "usage_metadata": None})()

    class FakeClient:
        models = FakeModels()

    timestamps = iter([1.0, 2.25])
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(timestamps))

    assert ask_module.ask("question") == "answer"
    assert "[応答時間] 1.25秒" in capsys.readouterr().out
