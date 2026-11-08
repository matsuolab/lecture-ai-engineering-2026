"""第1回: 素のLLMに質問するスクリプト（会話履歴を保ったまま続けて質問できる）。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    # 回答のあと続けて質問できる。空Enter / exit / Ctrl-D で終了

ツールは持たない「素の」呼び出し。会話履歴は毎回まとめて送り直すので、
質問を重ねるほど入力トークンが増えることも確かめよう。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(
    question: str, history: list[types.Content] | None = None
) -> tuple[str, int | None, int | None]:
    """質問を history に追加し、履歴ごとLLMに送る。回答も history に追加する。"""
    if history is None:
        history = []
    client = genai.Client(api_key=get_api_key())
    history.append(types.Content(role="user", parts=[types.Part(text=question)]))
    response = client.models.generate_content(model=MODEL, contents=history)
    history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    return response.text, input_tokens, output_tokens


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    history: list[types.Content] = []
    question = args.question
    while True:
        print(f"[質問] {question}\n")
        try:
            answer, input_tokens, output_tokens = ask(question, history)
            print(answer)
            print(f"\n[tokens] 入力: {input_tokens if input_tokens is not None else '不明'}, "
                  f"出力: {output_tokens if output_tokens is not None else '不明'}")
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        try:
            question = input("\n次の質問（空Enter / exit / Ctrl-D で終了）> ").strip()
        except EOFError:
            break
        if question in ("", "exit", "quit"):
            break


if __name__ == "__main__":
    main()
