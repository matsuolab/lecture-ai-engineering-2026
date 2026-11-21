"""複数のGeminiモデルと質問を比較し、時間・トークン・レート枠を集計する。"""

import argparse
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from google import genai
from google.genai import errors

from app.config import DEFAULT_MODEL, api_error_message, get_api_key

PACIFIC = ZoneInfo("America/Los_Angeles")


@dataclass(frozen=True)
class RateLimits:
    rpm: int | None
    tpm: int | None
    rpd: int | None


@dataclass(frozen=True)
class ComparisonRecord:
    timestamp: datetime
    pacific_date: date
    elapsed: float
    input_tokens: int
    output_tokens: int
    error: str | None = None


def _read_limit(model: str, name: str) -> int | None:
    model_key = re.sub(r"[^A-Z0-9]+", "_", model.upper()).strip("_")
    raw = os.getenv(f"AIE_{model_key}_{name}_LIMIT")
    if raw is None:
        raw = os.getenv(f"AIE_{name}_LIMIT")
    if raw is None:
        return None
    try:
        limit = int(raw)
    except ValueError:
        raise SystemExit(f"AIE_{name}_LIMIT は正の整数で指定してください") from None
    if limit <= 0:
        raise SystemExit(f"AIE_{name}_LIMIT は正の整数で指定してください")
    return limit


def load_rate_limits(model: str) -> RateLimits:
    """モデル固有の上限を優先し、なければ共通上限を使う。"""
    return RateLimits(
        rpm=_read_limit(model, "RPM"),
        tpm=_read_limit(model, "TPM"),
        rpd=_read_limit(model, "RPD"),
    )


def _limit_text(limit: int | None) -> str:
    return str(limit) if limit is not None else "未設定"


def _remaining_text(used: int, limit: int | None, unit: str) -> str:
    if limit is None:
        return "上限未設定"
    return f"{used}/{limit} {unit}（残り {max(0, limit - used)}）"


def _print_summary(
    model: str,
    records: list[ComparisonRecord],
    limits: RateLimits,
) -> None:
    now = datetime.now(UTC)
    recent = [record for record in records if now - record.timestamp < timedelta(minutes=1)]
    today = [record for record in records if record.pacific_date == now.astimezone(PACIFIC).date()]
    requests_per_minute = len(recent)
    input_tokens_per_minute = sum(record.input_tokens for record in recent)
    requests_per_day = len(today)
    input_tokens = sum(record.input_tokens for record in records)
    output_tokens = sum(record.output_tokens for record in records)
    elapsed = sum(record.elapsed for record in records)
    average_elapsed = elapsed / len(records) if records else 0

    print(f"\n=== {model} の集計 ===")
    print(
        f"RPM: {_limit_text(limits.rpm)} / "
        f"TPM（入力）: {_limit_text(limits.tpm)} / "
        f"RPD: {_limit_text(limits.rpd)}"
    )
    print(
        f"実行時間: 合計 {elapsed:.2f}秒 / 平均 {average_elapsed:.2f}秒、"
        f"入力: {input_tokens} tokens / 出力: {output_tokens} tokens"
    )
    print(
        "残量（この比較実行内の使用分を差し引いた概算）: "
        f"RPM {_remaining_text(requests_per_minute, limits.rpm, 'requests')} / "
        f"TPM {_remaining_text(input_tokens_per_minute, limits.tpm, 'tokens')} / "
        f"RPD {_remaining_text(requests_per_day, limits.rpd, 'requests')}"
    )


def compare(
    client: genai.Client,
    models: list[str],
    questions: list[str],
    limits_by_model: dict[str, RateLimits],
) -> None:
    records_by_model: dict[str, list[ComparisonRecord]] = {model: [] for model in models}

    for model in models:
        for index, question in enumerate(questions, start=1):
            started = time.perf_counter()
            try:
                response = client.models.generate_content(model=model, contents=question)
            except errors.APIError as error:
                elapsed = time.perf_counter() - started
                now = datetime.now(UTC)
                records_by_model[model].append(
                    ComparisonRecord(
                        timestamp=now,
                        pacific_date=now.astimezone(PACIFIC).date(),
                        elapsed=elapsed,
                        input_tokens=0,
                        output_tokens=0,
                        error=api_error_message(error.code, error.message),
                    )
                )
                print(f"\n[{model} / 質問{index}] {api_error_message(error.code, error.message)}")
                continue

            elapsed = time.perf_counter() - started
            now = datetime.now(UTC)
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count or 0 if usage else 0
            output_tokens = usage.candidates_token_count or 0 if usage else 0
            records_by_model[model].append(
                ComparisonRecord(
                    timestamp=now,
                    pacific_date=now.astimezone(PACIFIC).date(),
                    elapsed=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )
            print(f"\n[{model} / 質問{index}] {question}")
            print(response.text or "")
            print(
                f"[応答時間] {elapsed:.2f}秒 / "
                f"入力: {input_tokens} tokens / 出力: {output_tokens} tokens"
            )

    for model in models:
        _print_summary(model, records_by_model[model], limits_by_model[model])
    print("\n注: 使用量はこの比較実行中の観測分です。他プロセスの利用量は含みません。")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="複数モデル・複数質問の応答時間とトークン使用量を比較する"
    )
    parser.add_argument(
        "--model",
        dest="models",
        action="append",
        help=f"比較するモデル。複数回指定できます（既定: {DEFAULT_MODEL}）",
    )
    parser.add_argument(
        "--question",
        dest="questions",
        action="append",
        required=True,
        help="質問。複数回指定すると全モデルに同じ質問を送ります",
    )
    args = parser.parse_args()

    models = args.models or [DEFAULT_MODEL]
    limits_by_model = {model: load_rate_limits(model) for model in models}
    client = genai.Client(api_key=get_api_key())
    compare(client, models, args.questions, limits_by_model)


if __name__ == "__main__":
    main()