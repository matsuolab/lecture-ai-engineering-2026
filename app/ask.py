"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    # 回答後は質問を続けられる。終了するには「終了」または exit を入力する。

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

if __package__:
    from app.config import MODEL, api_error_message, get_api_key
else:
    from config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat, question: str) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[tokens] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return response.text


def run_conversation(chat, first_question: str, input_fn=input) -> None:
    question = first_question
    while True:
        print(f"[質問] {question}\n")
        print(ask(chat, question))

        try:
            question = input_fn("\n続けて質問してください（終了: 終了 / exit）: ").strip()
        except EOFError:
            break
        if question.lower() in {"終了", "exit", "quit"}:
            break
        if not question:
            continue


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    try:
        run_conversation(chat, args.question)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
