"""第1回: 素のLLMと会話するスクリプト。

使い方:
    uv run python -m app.ask

ツールは使わず、同じ Chat に質問を送り続けることで会話履歴を保つ。
質問は実行時に入力する。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 質問例。起動時の既定値としては使わない
EXAMPLE_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def main() -> None:
    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)

        while True:
            try:
                question = input("質問してください（終了するには空入力）: ").strip()
            except EOFError:
                print()
                break
            if not question:
                break

            print(f"[質問] {question}\n")
            started_at = time.perf_counter()
            response = chat.send_message(question)
            elapsed = time.perf_counter() - started_at
            print(f"{response.text}\n")
            print(f"[応答時間] {elapsed:.2f}秒")

            usage = response.usage_metadata
            if usage is not None:
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                print(
                    f"[トークン数] 入力: {input_tokens if input_tokens is not None else '不明'}, "
                    f"出力: {output_tokens if output_tokens is not None else '不明'}\n"
                )
            else:
                print("[トークン数] 使用量情報を取得できませんでした。\n")
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
