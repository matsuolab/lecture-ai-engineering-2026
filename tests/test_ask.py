from types import SimpleNamespace
from unittest.mock import Mock

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="回答",
    )
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask.genai,
        "Client",
        Mock(return_value=SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(return_value=response)
            )
        )),
    )

    assert ask.ask("質問") == "回答"
    assert capsys.readouterr().out == "[tokens] 入力: 12 / 出力: 34\n"


def test_ask_returns_response_when_usage_metadata_is_missing(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="回答")
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask.genai,
        "Client",
        Mock(return_value=SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(return_value=response)
            )
        )),
    )

    assert ask.ask("質問") == "回答"
    assert capsys.readouterr().out == ""
