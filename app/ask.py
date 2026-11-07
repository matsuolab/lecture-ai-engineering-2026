"""第1回: ツールを使わず、LLMとの会話を続けるスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

回答の後に質問を入力すると、会話履歴を保ったまま続けて質問できる。
空行を入力すると終了する。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from time import perf_counter

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat: genai.chats.Chat) -> genai.types.GenerateContentResponse:
    return chat.send_message(question)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        question = args.question

        while True:
            print(f"[質問] {question}\n")
            started_at = perf_counter()
            response = ask(question, chat)
            print(response.text)
            elapsed = perf_counter() - started_at

            usage = response.usage_metadata
            if usage is None:
                print("[usage] トークン使用量を取得できませんでした")
            else:
                print(
                    f"[usage] input_tokens={usage.prompt_token_count}, "
                    f"output_tokens={usage.candidates_token_count}"
                )
            print(f"[応答時間] {elapsed:.2f} 秒\n")

            try:
                question = input("[続けて質問（終了するには空行）] ")
            except EOFError:
                break
            if not question.strip():
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
