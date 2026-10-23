"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --interactive  # 会話履歴を保って続けて質問する

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）

--interactive を指定した場合は、終了するまで同じ会話で質問を続ける。
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat: genai.chats.Chat | None = None) -> str:
    if chat is None:
        client = genai.Client(api_key=get_api_key())
        response = client.models.generate_content(model=MODEL, contents=question)
    else:
        response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(f"[usage] 入力トークン数: {usage.prompt_token_count}, 出力トークン数: {usage.candidates_token_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="会話履歴を保って続けて質問する（終了: exit または quit）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.interactive:
            client = genai.Client(api_key=get_api_key())
            chat = client.chats.create(model=MODEL)
            question = args.question
            while True:
                if question is None:
                    try:
                        question = input("質問（終了: exit）: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print()
                        break
                    if question.lower() in {"exit", "quit"}:
                        break
                    if not question:
                        continue

                print(f"[質問] {question}\n")
                print(ask(question, chat))
                question = None
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
