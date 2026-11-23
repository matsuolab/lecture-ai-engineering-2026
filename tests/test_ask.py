from types import SimpleNamespace

from app.ask import format_usage_summary


def test_format_usage_summary_uses_prompt_and_candidates_token_counts():
    usage = SimpleNamespace(
        prompt_token_count=123,
        candidates_token_count=45,
        total_token_count=168,
    )

    assert format_usage_summary(usage) == "入力トークン数: 123, 出力トークン数: 45"
