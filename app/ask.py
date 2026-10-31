"""Flash、Flash-Lite、Gemmaの回答とtemperatureを比較するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask

各系列で利用可能な最新モデルから順に試し、temperature 0.2と1.0の回答を表示する。
次のターンに使う回答を選び、全モデルに同じ会話履歴を渡す。
"""

import argparse
import re
from time import perf_counter

# Gemini SDKの会話履歴はContent形式で渡すため、その型と履歴引数用のSequenceを使う。
from collections.abc import Sequence
from dataclasses import dataclass

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
# 各ターンで同じ質問・履歴に対する回答を比較する。
TEMPERATURES = (0.2,)
MODEL_FAMILIES = ("Flash", "Flash-Lite", "Gemma")
MAX_MODEL_VERSIONS = 3


@dataclass(frozen=True)
class AskResult:
    """表示用の回答文と、会話履歴に使うSDKの応答を保持する。"""

    text: str
    content: types.Content


class EmptyModelResponseError(RuntimeError):
    """モデルが会話に追加できる回答を返さなかったことを示す。"""


def _model_id(model: types.Model) -> str:
    """モデル一覧のリソース名からAPI呼び出し用のモデルIDを取り出す。"""
    return (model.name or "").rsplit("/", maxsplit=1)[-1]


def _model_family(model_id: str) -> str | None:
    """モデルIDを比較対象の系列に分類する。"""
    model_id = model_id.lower()
    if model_id.startswith("gemma-"):
        return "Gemma"
    if model_id.startswith("gemini-") and "flash-lite" in model_id:
        return "Flash-Lite"
    if model_id.startswith("gemini-") and "flash" in model_id:
        return "Flash"
    return None


def _model_sort_key(model_id: str) -> tuple[bool, tuple[int, ...], bool, int, str]:
    """latest別名、バージョン、安定版、Gemmaのパラメーター数で候補を並べる。"""
    version_match = re.search(r"(?:gemini|gemma)-(\d+(?:\.\d+)*)", model_id)
    version = (
        tuple(int(part) for part in version_match.group(1).split("."))
        if version_match
        else ()
    )
    parameter_match = re.search(r"-(\d+)b(?:-|$)", model_id)
    parameter_count = int(parameter_match.group(1)) if parameter_match else 0
    return (
        model_id.endswith("-latest"),
        version,
        "preview" not in model_id,
        parameter_count,
        model_id,
    )


def discover_model_candidates() -> dict[str, tuple[str, ...]]:
    """APIが利用可能と返すモデルから、各系列の新しい候補を最大3件選ぶ。"""
    client = genai.Client(api_key=get_api_key())
    candidates: dict[str, list[str]] = {family: [] for family in MODEL_FAMILIES}
    for model in client.models.list():
        model_id = _model_id(model)
        family = _model_family(model_id)
        if family is None:
            continue
        if (
            model.supported_actions is not None
            and "generateContent" not in model.supported_actions
        ):
            continue
        candidates[family].append(model_id)

    ordered: dict[str, tuple[str, ...]] = {}
    for family, model_ids in candidates.items():
        model_ids.sort(key=_model_sort_key, reverse=True)
        if family == "Gemma":
            # Gemmaは同じ世代にサイズ違いが複数あるため、旧世代へ順にフォールバックする。
            unique_versions: dict[tuple[int, ...], str] = {}
            for model_id in model_ids:
                match = re.search(r"gemma-(\d+(?:\.\d+)*)", model_id)
                version = (
                    tuple(int(part) for part in match.group(1).split("."))
                    if match
                    else ()
                )
                unique_versions.setdefault(version, model_id)
            model_ids = list(unique_versions.values())
        ordered[family] = tuple(model_ids[:MAX_MODEL_VERSIONS])
    return ordered


def ask(
    question: str,
    temperature: float = 0.2,
    history: Sequence[types.Content] = (),
    model_name: str = MODEL,
) -> AskResult:
    """共通の会話履歴と質問を指定temperatureでモデルに送り、回答を返す。"""
    client = genai.Client(api_key=get_api_key())
    # 過去の会話の後ろに今回の質問を追加し、同じ履歴を各temperatureに渡す。
    contents = [
        *history,
        types.Content(role="user", parts=[types.Part(text=question)]),
    ]
    start_time = perf_counter()
    response = client.models.generate_content(
        # 呼び出し元が選んだモデルを使い、temperatureだけを比較対象にする。
        model=model_name,
        contents=contents,
        config={"temperature": temperature, "max_output_tokens": 300},
    )
    response_time = perf_counter() - start_time

    # APIがトークン使用量を返さない場合もあるため、不明として表示する。
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    print(
        f"[トークン] 入力: {input_tokens if input_tokens is not None else '不明'} / "
        f"出力: {output_tokens if output_tokens is not None else '不明'}"
    )
    print(f"[応答時間] {response_time:.2f}秒")

    # 回答本文だけで作り直すとthought signatureなどSDK応答の情報が失われる。
    candidates = response.candidates
    if not candidates or candidates[0].content is None or response.text is None:
        raise EmptyModelResponseError("モデルから会話に使えるテキスト回答がありませんでした。")
    return AskResult(text=response.text, content=candidates[0].content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flash、Flash-Lite、Gemmaの回答を比較する"
    )
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    try:
        model_candidates = discover_model_candidates()
    except errors.APIError as e:
        print(f"[エラー] モデル一覧を取得できませんでした: {api_error_message(e.code, e.message)}")
        raise SystemExit(1) from e

    # 両条件の比較で共有する履歴。会話開始時は空にする。
    history: list[types.Content] = []
    question = args.question
    print(f"[質問] {question}")

    while True:
        successful_answers: dict[str, tuple[str, dict[float, AskResult]]] = {}
        for family in MODEL_FAMILIES:
            family_candidates = model_candidates[family]
            if not family_candidates:
                print(f"\n[候補なし] {family} 系列の利用可能なモデルがありません。")
                continue

            for model_name in family_candidates:
                answers: dict[float, AskResult] = {}
                print(f"\n[モデル確認] {family}: {model_name}")
                try:
                    for temperature in TEMPERATURES:
                        answers[temperature] = ask(
                            question, temperature, history, model_name
                        )
                except EmptyModelResponseError as e:
                    print(f"[失敗] {model_name}: {e}")
                except errors.APIError as e:
                    print(
                        f"[失敗] {model_name}: "
                        f"{api_error_message(e.code, e.message)}"
                    )
                else:
                    successful_answers[family] = (model_name, answers)
                    break

            if family not in successful_answers:
                print(f"[失敗] {family} 系列で利用できるモデルがありませんでした。")

        if not successful_answers:
            print("[エラー] 利用できるモデルがありません。モデル設定を確認してください。")
            raise SystemExit(1)

        answer_options: dict[str, AskResult] = {}
        print("\n[比較結果]")
        for family in MODEL_FAMILIES:
            if family not in successful_answers:
                continue
            model_name, answers = successful_answers[family]
            print(f"\n[{family}] 使用モデル: {model_name}")
            for temperature in TEMPERATURES:
                answer = answers[temperature]
                print(f"\n[temperature] {temperature}")
                print(answer.text)
                option = str(len(answer_options) + 1)
                answer_options[option] = answer
                print(f"[選択肢 {option}] {family} / temperature {temperature}")

        # 選んだ系列・temperatureの回答だけを、次の会話履歴に使う。
        while True:
            choice = input(
                "\n次の会話に使う回答の選択肢番号を入力してください (q: 終了): "
            ).strip().lower()
            if choice == "q":
                break
            if choice in answer_options:
                selected_answer = answer_options[choice]
                break
            print("選択を読み取れませんでした。表示された番号、または q を入力してください。")

        if choice == "q":
            break

        # 選ばれた回答だけを履歴に追加し、次ターンも両条件で共有する。
        history.extend(
            [
                types.Content(
                    role="user",
                    parts=[types.Part(text=question)],
                ),
                selected_answer.content,
            ]
        )
        # 続きの質問を受け取り、qまたは空入力なら会話を終える。
        question = input("\n次の質問 (終了: q): ").strip()
        if question.lower() == "q":
            break
        if not question:
            print("質問が空なので終了します。")
            break


if __name__ == "__main__":
    main()
