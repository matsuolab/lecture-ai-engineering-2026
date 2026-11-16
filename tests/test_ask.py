from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=5),
    )

    class FakeClient:
        class models:
            @staticmethod
            def generate_content(*, model, contents):
                return response

    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask.genai, "Client", lambda **kwargs: FakeClient())

    assert ask.ask("質問") == "回答"
    assert capsys.readouterr().out == "[tokens] 入力: 12 / 出力: 5\n"