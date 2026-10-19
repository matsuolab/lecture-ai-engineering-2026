from types import SimpleNamespace

import pytest

from app import ask as ask_module


@pytest.mark.parametrize(
    ("usage_metadata", "expected"),
    [
        (SimpleNamespace(prompt_token_count=12, candidates_token_count=7), "[トークン] 入力: 12, 出力: 7\n"),
        (None, "[トークン] 入力: 不明, 出力: 不明\n"),
    ],
)
def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys, usage_metadata, expected):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=usage_metadata,
    )
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: response))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out == expected