"""会話履歴を保持してGeminiと対話するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask

終了:
    exit または quit を入力するか、Ctrl+Cを押す。

会話履歴は実行中のみ保持する。
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    """質問を1回送信し、トークン数を表示して回答テキストを返す。"""
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")
    return response.text or "（テキストの回答がありません）"


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保持してGeminiと対話する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print("追加の質問を入力できます。終了するには exit / quit または Ctrl+C。\n")

    # クライアントとチャットは最初に1回だけ作る。
    with genai.Client(api_key=get_api_key()) as client:
        chat = client.chats.create(model=MODEL)
        question = args.question

        while True:
            print(f"[質問] {question}\n")

            try:
                # 同じchatを使うことで、それまでの会話が引き継がれる。
                response = chat.send_message(message=question)

                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count if usage else None
                output_tokens = usage.candidates_token_count if usage else None

                print(f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}")
                print(f"[回答]\n{response.text or '（テキストの回答がありません）'}\n")

            except errors.APIError as e:
                print(api_error_message(e.code, e.message))
                print("質問を入力し直してください。\n")

            # 空の入力は送信せず、再入力を待つ。
            while True:
                question = input("あなた > ").strip()

                if question.lower() in {"exit", "quit"}:
                    print("会話を終了します。")
                    return

                if question:
                    break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n会話を終了します。")