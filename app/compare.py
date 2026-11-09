"""複数のGeminiモデル・質問を順番に実行して比較する。"""

import argparse
import time
from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from app.config import DEFAULT_MODEL, api_error_message, get_api_key


@dataclass
class Trial:
    model: str
    question: str
    elapsed_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    answer: str | None
    error: str | None
    status_code: int | None


def run_trial(client: genai.Client, model: str, question: str) -> Trial:
    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(temperature=2.0),
    )
    started_at = time.perf_counter()
    try:
        response = chat.send_message(question)
    except errors.APIError as error:
        elapsed_seconds = time.perf_counter() - started_at
        return Trial(
            model=model,
            question=question,
            elapsed_seconds=elapsed_seconds,
            input_tokens=None,
            output_tokens=None,
            answer=None,
            error=api_error_message(error.code, error.message),
            status_code=error.code,
        )

    elapsed_seconds = time.perf_counter() - started_at
    usage = response.usage_metadata
    return Trial(
        model=model,
        question=question,
        elapsed_seconds=elapsed_seconds,
        input_tokens=usage.prompt_token_count if usage else None,
        output_tokens=usage.candidates_token_count if usage else None,
        answer=response.text,
        error=None,
        status_code=None,
    )


def run_comparison(
    models: list[str],
    questions: list[str],
    delay_seconds: float = 1.0,
    repeats: int = 1,
) -> list[Trial]:
    if delay_seconds < 0:
        raise ValueError("リクエスト間隔は0秒以上にしてください。")
    if repeats < 1:
        raise ValueError("繰り返し回数は1回以上にしてください。")

    client = genai.Client(api_key=get_api_key())
    trials = []
    requests = [
        (model, question)
        for question in questions
        for model in models
        for _ in range(repeats)
    ]

    for index, (model, question) in enumerate(requests):
        trial = run_trial(client, model, question)
        trials.append(trial)
        print(f"\n[{index + 1}/{len(requests)}] {model} | {question}")
        if trial.error:
            print(f"エラー: {trial.error}")
            if trial.status_code == 429:
                print("レート制限を検出したため、残りの試行を中止します。")
                break
        else:
            print(f"応答時間: {trial.elapsed_seconds:.2f}秒")
            print(f"トークン: 入力 {trial.input_tokens}, 出力 {trial.output_tokens}")
            print(f"回答:\n{trial.answer}")

        if index < len(requests) - 1:
            time.sleep(delay_seconds)

    print("\n比較結果")
    print("| モデル | 質問 | 秒 | 入力tokens | 出力tokens | 状態 |")
    print("|---|---|---:|---:|---:|---|")
    for trial in trials:
        status = "成功" if trial.error is None else trial.error
        input_tokens = "-" if trial.input_tokens is None else trial.input_tokens
        output_tokens = "-" if trial.output_tokens is None else trial.output_tokens
        question = trial.question.replace("|", "\\|")
        print(
            f"| {trial.model} | {question} | {trial.elapsed_seconds:.2f} "
            f"| {input_tokens} | {output_tokens} | {status} |"
        )
    return trials


def main() -> None:
    parser = argparse.ArgumentParser(
        description="複数モデル・質問を比較し、応答時間とトークン数を表示する"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=[DEFAULT_MODEL],
        help="比較するモデル名（複数指定可）",
    )
    parser.add_argument(
        "--questions",
        nargs="+",
        required=True,
        help="比較する質問（複数指定可。空白を含む質問は引用符で囲む）",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="APIリクエスト間の待ち時間（秒、既定: 1）",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="各モデル・質問の繰り返し回数（既定: 1）",
    )
    args = parser.parse_args()

    try:
        run_comparison(args.models, args.questions, args.delay, args.repeats)
    except errors.APIError as error:
        print(api_error_message(error.code, error.message))
        raise SystemExit(1) from error
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
