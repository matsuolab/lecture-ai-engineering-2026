"""素のLLM呼び出しの表示テスト（LLMもAPIキーも使わない）。"""

from types import SimpleNamespace

from app import ask as ask_module


def test_ask_displays_token_counts_and_response_time(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
    )

    def generate_content(*, model: str, contents: str) -> SimpleNamespace:
        assert model == ask_module.MODEL
        assert contents == "質問"
        return response

    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )

    def create_client(*, api_key: str) -> SimpleNamespace:
        assert api_key == "test-key"
        return client

    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    times = iter([10.0, 11.234])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(times))

    assert ask_module.ask("質問") == "回答"

    output = capsys.readouterr().out
    assert "[入力トークン数] 12" in output
    assert "[出力トークン数] 34" in output
    assert "[応答時間] 1.23秒" in output


def test_ask_displays_unknown_when_usage_metadata_is_unavailable(monkeypatch, capsys):
    response = SimpleNamespace(text="回答", usage_metadata=None)

    def generate_content(*, model: str, contents: str) -> SimpleNamespace:
        assert model == ask_module.MODEL
        assert contents == "質問"
        return response

    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )

    def create_client(*, api_key: str) -> SimpleNamespace:
        assert api_key == "test-key"
        return client

    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    times = iter([10.0, 11.0])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(times))

    assert ask_module.ask("質問") == "回答"

    output = capsys.readouterr().out
    assert "[入力トークン数] 不明" in output
    assert "[出力トークン数] 不明" in output
