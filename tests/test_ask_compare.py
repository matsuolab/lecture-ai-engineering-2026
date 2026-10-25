from types import SimpleNamespace
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from app import ask_compare


def test_compare_question_uses_both_models_and_records_metrics():
    calls = []
    responses = iter(
        [
            SimpleNamespace(
                usage_metadata=SimpleNamespace(candidates_token_count=21),
                text="モデルAの回答",
            ),
            SimpleNamespace(
                usage_metadata=SimpleNamespace(candidates_token_count=14),
                text="モデルBの回答",
            ),
        ]
    )

    def generate_content(**kwargs):
        calls.append(kwargs)
        return next(responses)

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    with patch("app.ask_compare.perf_counter", side_effect=[1.0, 1.25, 2.0, 2.4]):
        results = ask_compare.compare_question(client, "LoRAとは？")

    assert [call["model"] for call in calls] == list(ask_compare.MODELS)
    assert all(call["contents"] == "LoRAとは？" for call in calls)
    assert [round(result.response_seconds, 2) for result in results] == [0.25, 0.4]
    assert [result.output_tokens for result in results] == [21, 14]
    assert [result.answer for result in results] == ["モデルAの回答", "モデルBの回答"]
    table = ask_compare.format_results(results)
    assert "| 質問 | モデル | 応答時間 (秒) | 出力トークン数 | 結果 |" in table
    assert "| LoRAとは？ | gemini-3.8-flash | 0.25 | 21 | 成功 |" in table


def test_main_prints_each_answer_with_its_model_name():
    results = [
        ask_compare.ComparisonResult(
            question="LoRAとは？",
            model="gemini-3.8-flash",
            response_seconds=0.5,
            output_tokens=10,
            answer="3.8の回答",
        ),
        ask_compare.ComparisonResult(
            question="LoRAとは？",
            model="gemini-3.5-flash-lite",
            response_seconds=0.7,
            output_tokens=12,
            answer="3.5-liteの回答",
        ),
    ]
    output = StringIO()

    with (
        patch("app.ask_compare.genai.Client"),
        patch("app.ask_compare.get_api_key", return_value="test-key"),
        patch("app.ask_compare.compare_question", return_value=results),
        patch("builtins.input", side_effect=["LoRAとは？", ""]),
        redirect_stdout(output),
    ):
        ask_compare.main()

    printed = output.getvalue()
    assert "--- gemini-3.8-flash の回答 ---" in printed
    assert "3.8の回答" in printed
    assert "--- gemini-3.5-flash-lite の回答 ---" in printed
    assert "3.5-liteの回答" in printed