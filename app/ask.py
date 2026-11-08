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

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(
    question: str, history: list[dict[str, str]] | None = None
) -> tuple[str, list[dict[str, str]]]:
    client = genai.Client(api_key=get_api_key())
    updated_history = list(history or [])
    contents = [
        types.Content(
            role=message["role"],
            parts=[types.Part(text=message["text"])],
        )
        for message in updated_history
    ]
    contents.append(
        types.Content(role="user", parts=[types.Part(text=question)])
    )
    response = client.models.generate_content(model=MODEL, contents=contents)

    # TODO(第1回 演習): response.usage_metadata から
    usage = getattr(response, "usage_metadata", None)
    if usage:
        prompt_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        print(f"入力: {prompt_tokens} tokens / 出力: {output_tokens} tokens")

    answer = response.text
    updated_history.extend(
        [
            {"role": "user", "text": question},
            {"role": "model", "text": answer},
        ]
    )
    return answer, updated_history

def chat(first_question: str) -> None:
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL) # 履歴は SDK の Chat が持つ
    question = first_question
    while question:
        response = session.send_message(question) # これまでの履歴＋今回の質問を送る
        print(response.text)
        usage = response.usage_metadata
        print(f"[tokens] 入力 {usage.prompt_token_count} / 出力 {usage.candidates_token_count}")
        question = input("\n[続けて質問（空行で終了）] ").strip()

def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        answer, _ = ask(args.question)
        print(answer)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()