from types import SimpleNamespace

from app import ask as ask_module


class FakeModels:
    def __init__(self, response):
        self.response = response

    def generate_content(self, **kwargs):
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def run_ask(monkeypatch, response, capsys):
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **kwargs: FakeClient(response),
    )

    answer = ask_module.ask("テスト質問")
    return answer, capsys.readouterr().out


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="テスト回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=7,
        ),
    )

    answer, output = run_ask(monkeypatch, response, capsys)

    assert answer == "テスト回答"
    assert "入力: 12" in output
    assert "出力: 7" in output


def test_ask_handles_missing_usage_metadata(monkeypatch, capsys):
    response = SimpleNamespace(text="テスト回答", usage_metadata=None)

    _, output = run_ask(monkeypatch, response, capsys)

    assert "入力: 不明" in output
    assert "出力: 不明" in output
