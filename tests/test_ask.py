import sys
from types import SimpleNamespace

import pytest

from app import ask as ask_module


@pytest.mark.parametrize(
    ("cli_args", "expected_temperature"),
    [
        (["--temperature", "0.25", "question"], 0.25),
        (["question"], None),
    ],
)
def test_main_temperature_and_existing_output(
    cli_args, expected_temperature, monkeypatch, capsys
):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(
            prompt_token_count=2,
            candidates_token_count=3,
            total_token_count=5,
        ),
    )
    calls = []
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: (calls.append(kwargs), response)[1]
        )
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", *cli_args])

    ask_module.main()

    output = capsys.readouterr().out
    call = calls[0]
    assert call["contents"] == "question"
    if expected_temperature is None:
        assert "config" not in call
        assert "[temperature] モデル既定値" in output
    else:
        assert call["config"].temperature == expected_temperature
        assert "[temperature] 0.25" in output
    assert "answer" in output
    assert "入力: 2" in output
    assert "出力: 3" in output
    assert "合計: 5" in output