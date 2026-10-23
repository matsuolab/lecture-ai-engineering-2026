"""計測スクリプトのテスト(LLMもAPIキーも使わない)。"""

from types import SimpleNamespace

from google.genai import errors

import measure_llm


def fake_usage(prompt=10, output=100, thoughts=None):
    return SimpleNamespace(
        prompt_token_count=prompt,
        candidates_token_count=output,
        thoughts_token_count=thoughts,
        total_token_count=prompt + output + (thoughts or 0),
    )


def ok_record(latency_s, ttft_s, output=100, thoughts=None):
    chunks = [[ttft_s, 1, None], [latency_s, 1, output]]
    return measure_llm.build_record(
        "m", "short", 1, latency_s, chunks=chunks, usage=fake_usage(output=output, thoughts=thoughts), text="a"
    )


def test_build_record_derives_ttft_and_output_time_from_chunks():
    record = ok_record(latency_s=5.0, ttft_s=2.0)
    assert record["status"] == measure_llm.STATUS_OK
    assert (record["ttft_s"], record["output_s"], record["n_chunks"]) == (2.0, 3.0, 2)


def test_build_record_treats_missing_thoughts_as_zero():
    assert ok_record(1.0, 0.5)["thinking_tokens"] == 0
    assert ok_record(1.0, 0.5, thoughts=40)["thinking_tokens"] == 40


def test_build_record_keeps_error_status():
    error = errors.APIError(429, {"error": {"message": "quota"}})
    record = measure_llm.build_record("m", "short", 1, 0.5, error=error)
    assert record["status"] == 429
    assert "text" not in record


def test_summarize_separates_errors_from_successes():
    records = [
        ok_record(2.0, 1.0, output=100),  # 出力 1.0 秒 → 100 tokens/s
        ok_record(4.0, 1.0, output=300),  # 出力 3.0 秒 → 100 tokens/s
        measure_llm.build_record("m", "short", 3, 0.1, error=errors.APIError(429, {})),
    ]
    (row,) = measure_llm.summarize(records, ("model",))
    assert (row["n_ok"], row["n_error"]) == (2, 1)
    assert row["latency_median"] == 3.0
    assert row["output_tokens"] == 200
    assert row["tokens_per_s"] == 100.0
