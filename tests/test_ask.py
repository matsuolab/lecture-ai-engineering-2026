from types import SimpleNamespace

from app import ask as ask_module


class _DummyModels:
    def generate_content(self, model, contents):
        return SimpleNamespace(
            text="回答",
            usage_metadata=SimpleNamespace(
                prompt_token_count=123,
                candidates_token_count=456,
            ),
        )


class _DummyClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = _DummyModels()


def test_ask_prints_token_usage(monkeypatch, capsys):
    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: _DummyClient(api_key))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "dummy-key")

    result = ask_module.ask("hello")

    captured = capsys.readouterr()
    assert result == "回答"
    assert "[input_tokens] 123" in captured.out
    assert "[output_tokens] 456" in captured.out


def test_main_auto_loads_and_saves_history(tmp_path, monkeypatch):
    seen = {}

    class _HistoryModels:
        def generate_content(self, model, contents):
            seen["contents"] = contents
            return SimpleNamespace(
                text="次の回答",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=123,
                    candidates_token_count=456,
                ),
            )

    history_file = tmp_path / ".ask_history.txt"
    history_file.write_text("ユーザー: 前の質問\nアシスタント: 前の回答\n", encoding="utf-8")

    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: SimpleNamespace(models=_HistoryModels()))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "dummy-key")

    monkeypatch.setattr(ask_module, "DEFAULT_HISTORY_FILE", history_file)

    ask_module.main_for_test(question="続けて質問", history_file=history_file)

    assert "前の質問" in seen["contents"]
    assert "続けて質問" in seen["contents"]
    assert "ユーザー: 続けて質問" in history_file.read_text(encoding="utf-8")
