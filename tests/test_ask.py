"""実際のAPIを呼ばず、会話履歴と対話入力の動作を確認する。"""

import pytest
from google.genai import models, types

from app import ask


@pytest.fixture
def requests(monkeypatch):
    sent = []

    def generate_content(self, *, model, contents, config=None):
        sent.append(contents)
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text="ダミーの回答")]
                    ),
                    finish_reason="STOP",
                )
            ],
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=10, candidates_token_count=5
            ),
        )

    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(models.Models, "generate_content", generate_content)
    return sent


def test_followup_includes_previous_question_and_answer(monkeypatch, requests, capsys):
    monkeypatch.setattr("sys.argv", ["ask", "LoRAとは？"])
    inputs = iter(["  ", "  それを一言で説明して  ", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    ask.main()

    assert len(requests) == 2  # 空の入力ではAPIを呼ばない
    assert [(c.role, c.parts[0].text) for c in requests[1]] == [
        ("user", "LoRAとは？"),
        ("model", "ダミーの回答"),
        ("user", "それを一言で説明して"),
    ]
    assert "[トークン] 入力: 10, 出力: 5" in capsys.readouterr().out


@pytest.mark.parametrize("ending", ["exit", "QUIT", EOFError, KeyboardInterrupt])
def test_default_question_and_clean_exit(monkeypatch, requests, ending):
    monkeypatch.setattr("sys.argv", ["ask"])

    def read_input(_):
        if isinstance(ending, str):
            return ending
        raise ending

    monkeypatch.setattr("builtins.input", read_input)

    ask.main()

    assert len(requests) == 1
    assert requests[0][0].parts[0].text == ask.DEFAULT_QUESTION


def test_api_error_keeps_friendly_message(monkeypatch, requests, capsys):
    monkeypatch.setattr("sys.argv", ["ask", "LoRAとは？"])

    def fail(self, **kwargs):
        raise ask.errors.APIError(429, {"error": {"message": "rate limit"}})

    monkeypatch.setattr(models.Models, "generate_content", fail)

    with pytest.raises(SystemExit) as exc:
        ask.main()

    assert exc.value.code == 1
    assert "レート制限に達しました" in capsys.readouterr().out
