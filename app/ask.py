"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

会話履歴はアプリ内のメモリに保存され、起動中は続けて質問できる。
「終了」または exit / quit で終了する。
ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


class Conversation:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=get_api_key())
        self.history: list[genai.types.Content] = []

    def ask(self, question: str) -> str:
        user_message = genai.types.Content(
            role="user",
            parts=[genai.types.Part.from_text(text=question)],
        )
        started_at = time.perf_counter()
        response = self.client.models.generate_content(
            model=MODEL,
            contents=[*self.history, user_message],
        )
        elapsed = time.perf_counter() - started_at
        print(f"[応答時間] {elapsed:.2f}秒")

        usage = response.usage_metadata
        if usage is not None:
            print(f"[トークン数] 入力: {usage.prompt_token_count}, 出力: {usage.candidates_token_count}")

        if response.text is None:
            raise RuntimeError("モデルからテキスト回答が返りませんでした")

        self.history.extend(
            [
                user_message,
                genai.types.Content(
                    role="model",
                    parts=[genai.types.Part.from_text(text=response.text)],
                ),
            ]
        )
        return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    question = args.question
    conversation = Conversation()
    try:
        while True:
            print(f"[質問] {question}\n")
            print(conversation.ask(question))
            while True:
                try:
                    question = input("\n次の質問（終了するには「終了」と入力）: ").strip()
                except EOFError:
                    return
                if question.lower() in {"終了", "exit", "quit"}:
                    return
                if question:
                    break
                print("質問を入力してください。")
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
