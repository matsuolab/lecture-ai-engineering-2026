from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.ask import ask


def test_ask_prints_usage_metadata(capsys):
    response = SimpleNamespace(
        text="答え",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
            total_token_count=46,
        ),
    )

    with patch("app.ask.get_api_key", return_value="secret"), patch(
        "app.ask.genai.Client"
    ) as client_cls:
        client = Mock()
        client.models.generate_content.return_value = response
        client_cls.return_value = client

        result = ask("LoRAとは何ですか？")

    assert result == "答え"
    out = capsys.readouterr().out
    assert "入力トークン数" in out
    assert "12" in out
    assert "出力トークン数" in out
    assert "34" in out
