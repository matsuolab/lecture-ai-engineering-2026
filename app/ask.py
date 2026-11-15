"""第1回: 素のLLMに会話履歴を保って質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問のあと、続けて質問できる

ツールは使わず、Responses API の previous_response_id で会話履歴を保つ。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from openai import APIStatusError, OpenAI

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
    )

    # TODO(第1回 演習): response.usage から
    #   入力トークン数と出力トークン数を表示してみよう（Copilotに頼んでよい）

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("モデルからテキストの回答が返りませんでした")
    return content
class Conversation:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=get_api_key())
        self.previous_response_id: str | None = None

    def ask(self, question: str) -> str:
        request = {"model": MODEL, "input": question}
        if self.previous_response_id is not None:
            request["previous_response_id"] = self.previous_response_id
        response = self.client.responses.create(**request)

        if response.usage is not None:
            print(
                f"[usage] 入力トークン数: {response.usage.input_tokens}, "
                f"出力トークン数: {response.usage.output_tokens}"
            )
        else:
            print("[usage] トークン数を取得できませんでした")

        self.previous_response_id = response.id
        return response.output_text


def ask(question: str) -> str:
    """会話履歴を引き継がない単発の質問をする。"""
    return Conversation().ask(question)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        print(ask(args.question))
    except APIStatusError as e:
        print(api_error_message(e.status_code, e.message))
        conversation = Conversation()
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(conversation.ask(question))
            try:
                question = input("\n続けて質問してください（終了するには空行）: ").strip()
            except EOFError:
                print()
                break
            if not question:
                break
    except APIStatusError as e:
        print(api_error_message(e.status_code, str(e)))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
