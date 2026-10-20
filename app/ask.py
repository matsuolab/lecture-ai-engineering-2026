"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（第1回 宿題・実装）
    uv run python -m app.ask --chat "LoRAとは何ですか？"   # 最初の質問を指定して会話を始める

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）

LLM の API は呼び出しごとに状態を持たない（前の質問を覚えていない）。
--chat では、これまでのやり取りをリスト history にためて、毎回まとめて送り直すことで
会話を続けている。そのため、ターンが進むほど入力トークン数が増える。
"""

import argparse
from collections.abc import Callable

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

# 会話モードを終える入力
EXIT_WORDS = {"exit", "quit", "q", "終了"}


def print_usage(response: types.GenerateContentResponse) -> None:
    """応答の usage_metadata から入力・出力トークン数を表示する（第1回 演習）。"""
    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")


def ask(question: str) -> str:
    """1回だけ質問する（履歴なし）。"""
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    print_usage(response)
    return response.text


class Conversation:
    """会話履歴を保ったまま、続けて質問するためのクラス（第1回 宿題・実装）。

    history には、ユーザーの発話（role="user"）とモデルの応答（role="model"）が
    交互に入る。send() のたびに history 全体を contents として送る。
    """

    def __init__(self, client: genai.Client, model: str = MODEL) -> None:
        self.client = client
        self.model = model
        self.history: list[types.Content] = []

    def send(self, question: str) -> str:
        user_turn = types.Content(role="user", parts=[types.Part(text=question)])
        response = self.client.models.generate_content(
            model=self.model,
            contents=[*self.history, user_turn],
        )
        print_usage(response)

        # API 呼び出しが成功したときだけ履歴に足す。
        # 失敗したターン（レート制限など）を残すと、user が2回続く不正な履歴になるため。
        answer = response.text or ""
        self.history.append(user_turn)
        self.history.append(
            types.Content(role="model", parts=[types.Part(text=answer)])
        )
        return answer

    @property
    def turns(self) -> int:
        """これまでに成立した質問と応答の組の数。"""
        return len(self.history) // 2


def chat_loop(
    conversation: Conversation,
    first_question: str | None = None,
    input_fn: Callable[[str], str] = input,
) -> None:
    """標準入力から質問を読み、会話を続ける。空行か exit で終わる。"""
    print("会話モードです。空行または exit で終了します。\n")
    question = first_question
    while True:
        if question is None:
            try:
                question = input_fn("あなた> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
        if not question or question.lower() in EXIT_WORDS:
            break

        try:
            answer = conversation.send(question)
        except errors.APIError as e:
            # 1回の失敗で会話全体を終わらせない。履歴は失敗前のまま残る
            print(api_error_message(e.code, e.message))
        else:
            print(f"[履歴] {conversation.turns} ターン")
            print(f"\nモデル> {answer}\n")
        question = None


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保ったまま、続けて質問する",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")

    if args.chat:
        conversation = Conversation(genai.Client(api_key=get_api_key()))
        chat_loop(conversation, first_question=args.question)
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
