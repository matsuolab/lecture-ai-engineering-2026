
"""第1回: 会話履歴を保持してLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask

終了するには exit または quit と入力する。
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(chat, question: str) -> str:
    # 会話履歴を保持したまま質問する
    response = chat.send_message(question)

    # TODO(第1回 演習): response.usage_metadata から
    #   入力トークン数と出力トークン数を表示してみよう（Copilotに頼んでよい）
    usage = response.usage_metadata

    if usage:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")
        print(f"[合計トークン数] {usage.total_token_count}")

    return response.text or "(回答テキストがありません)"


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴付きLLMチャット")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    # チャットセッションを作成
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("チャットを開始します（終了: exit / quit）\n")

    question = args.question

    while True:
        try:
            print(f"\n[質問] {question}")
            answer = ask(chat, question)
            print(f"\n[回答]\n{answer}")

            # 次の質問を受け付ける
            question = input("\n次の質問 > ").strip()

            if question.lower() in ("exit", "quit"):
                print("チャットを終了します。")
                break

            if not question:
                continue

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

        except (KeyboardInterrupt, EOFError):
            print("\nチャットを終了します。")
            break


if __name__ == "__main__":
    main()
