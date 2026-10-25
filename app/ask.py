"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --interactive
    uv run python -m app.ask "LoRAとは何ですか？" --interactive

ツールは持たない「素の」呼び出しだが、対話モードでは会話履歴を保持する。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(
    question: str,
    history: list[types.Content] | None = None,
    client: genai.Client | None = None,
) -> str:
    """質問し、次回のために user/model のメッセージを履歴へ追加する。"""
    if client is None:
        client = genai.Client(api_key=get_api_key())
    if history is None:
        history = []

    user_message = types.Content(
        role="user", parts=[types.Part.from_text(text=question)]
    )
    response = client.models.generate_content(
        model=MODEL, contents=[*history, user_message]
    )

    # TODO(第1回 演習): response.usage_metadata から
    #   入力トークン数と出力トークン数を表示してみよう（Copilotに頼んでよい）
    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")
    else:
        print("[トークン数] 使用量の情報が返されませんでした")

    history.extend(
        [
            user_message,
            types.Content(
                role="model", parts=[types.Part.from_text(text=response.text)]
            ),
        ]
    )
    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", help="質問（省略時は対話モード）")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="回答後も質問を受け付け、会話履歴を保持する",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    interactive = args.interactive or args.question is None
    question = args.question or DEFAULT_QUESTION
    client = genai.Client(api_key=get_api_key())
    history: list[types.Content] = []

    try:
        while True:
            print(f"[質問] {question}\n")
            print(ask(question, history=history, client=client))
            if not interactive:
                break
            try:
                question = input("\n次の質問（終了するには空行または Ctrl-D）: ").strip()
            except EOFError:
                print()
                break
            if not question:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
