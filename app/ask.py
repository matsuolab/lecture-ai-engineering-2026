"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from google import genai
    from google.genai import errors
except ModuleNotFoundError:  # pragma: no cover - lazily handled in runtime paths
    genai = None
    errors = None

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
DEFAULT_COMPARISON_MODELS = tuple(
    dict.fromkeys(
        (MODEL, "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite")
    )
)[:3]


@dataclass
class ModelResult:
    model: str
    elapsed_seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    text: str | None = None
    error: str | None = None


def _token_counts(response: object) -> tuple[int | None, int | None]:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return None, None

    input_tokens = getattr(usage, "prompt_token_count", None)
    output_tokens = getattr(usage, "candidates_token_count", None)
    if input_tokens is None:
        input_tokens = getattr(usage, "input_tokens", None)
    if output_tokens is None:
        output_tokens = getattr(usage, "output_tokens", None)
    return input_tokens, output_tokens


def ask(question: str) -> str:
    """既定モデルに質問し、回答を返す。"""
    if genai is None:
        raise ModuleNotFoundError(
            "google-genai が未インストールです。`uv sync --frozen` を実行して依存関係を入れてください。"
        )

    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    input_tokens, output_tokens = _token_counts(response)
    if input_tokens is not None or output_tokens is not None:
        print(
            f"[token] 入力トークン: {input_tokens if input_tokens is not None else 'N/A'} "
            f"/ 出力トークン: {output_tokens if output_tokens is not None else 'N/A'}"
        )
    return response.text


def compare_models(question: str, models: tuple[str, ...]) -> list[ModelResult]:
    """同じ質問を各モデルへ送り、所要時間・トークン数・回答を集める。"""
    if genai is None:
        raise ModuleNotFoundError(
            "google-genai が未インストールです。`uv sync --frozen` を実行して依存関係を入れてください。"
        )

    client = genai.Client(api_key=get_api_key())
    results = []
    for model in models:
        started = time.perf_counter()
        try:
            response = client.models.generate_content(model=model, contents=question)
            elapsed = time.perf_counter() - started
            input_tokens, output_tokens = _token_counts(response)
            results.append(
                ModelResult(
                    model=model,
                    elapsed_seconds=elapsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    text=response.text,
                )
            )
        except Exception as e:
            if errors is None or not isinstance(e, errors.APIError):
                raise
            elapsed = time.perf_counter() - started
            results.append(
                ModelResult(
                    model=model,
                    elapsed_seconds=elapsed,
                    error=api_error_message(e.code, e.message),
                )
            )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="同じ質問を3つのモデルに送り、応答を比較する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--models",
        nargs=3,
        metavar=("MODEL1", "MODEL2", "MODEL3"),
        default=DEFAULT_COMPARISON_MODELS,
        help="比較する3つのGeminiモデル（既定: %(default)s）",
    )
    args = parser.parse_args()

    if len(set(args.models)) != 3:
        parser.error("--models には重複しないモデル名を3つ指定してください")

    print(f"[質問] {args.question}")
    try:
        results = compare_models(args.question, tuple(args.models))
    except ModuleNotFoundError as e:
        raise SystemExit(str(e))
    except Exception as e:
        if errors is not None and isinstance(e, errors.APIError):
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)
        raise

    for result in results:
        print(f"\n--- {result.model} ---")
        print(f"応答時間: {result.elapsed_seconds:.2f} 秒")
        print(f"入力トークン: {result.input_tokens if result.input_tokens is not None else 'N/A'}")
        print(f"出力トークン: {result.output_tokens if result.output_tokens is not None else 'N/A'}")
        if result.error is not None:
            print(f"エラー: {result.error}")
        else:
            print(f"応答:\n{result.text if result.text is not None else '（応答テキストなし）'}")

    if any(result.error is not None for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
