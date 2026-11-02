"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    # 回答後は続けて質問できます。終了するには /exit を入力します。

ツールは使わず、会話履歴を保って質問する「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat, question: str) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )
    else:
        print("[トークン] 使用量情報を取得できませんでした")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    try:
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(ask(chat, question))
            try:
                question = input("\n続けて質問してください（終了: /exit）: ").strip()
            except EOFError:
                break
            if question.lower() in {"/exit", "exit", "quit", "終了"}:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
