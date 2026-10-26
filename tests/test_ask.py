from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    class Models:
        def generate_content(self, **kwargs):
            assert kwargs["config"].temperature == 0.2
            return SimpleNamespace(
                text="answer",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=12,
                    candidates_token_count=7,
                ),
            )

    class Client:
        def __init__(self, *, api_key):
            self.models = Models()

    monkeypatch.setattr(ask.genai, "Client", Client)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")

    assert ask.ask("question", temperature=0.2) == "answer"
    output = capsys.readouterr().out
    assert "[入力トークン数] 12" in output
    assert "[出力トークン数] 7" in output