"""第1回: 素のLLMに会話履歴を引き継いで質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

回答後に次の質問を入力すると、同じ会話を続けられる。
exit / quit、Ctrl+C、EOF で終了する。履歴は実行中だけ保持する。
質問の送信から回答を受け取るまでの応答時間と、トークン数を表示する。

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from time import perf_counter

from google import genai
from google.genai import errors
from google.genai.chats import Chat

from app.config import MODEL, api_error_message, get_api_key
from dotenv import load_dotenv

load_dotenv()

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat: Chat) -> str:
    """同じ chat を使い、過去の質問と回答も含めて送信する。"""
    start = perf_counter()
    response = chat.send_message(
        question,
        # 温度関数を指定してランダム性を設定できる
        config={"temperature": 0.0})
    elapsed = perf_counter() - start
    print(f"[応答時間] {elapsed:.2f} 秒")

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return response.text or "（テキストの回答がありませんでした）"


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに会話履歴を引き継いで質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print("続けて質問できます。exit / quit、Ctrl+C、EOF で終了します。")
    try:
        with genai.Client(api_key=get_api_key()) as client:
            # 会話ごとに1つだけ作り、質問と回答の履歴をSDKに管理させる。
            chat = client.chats.create(model=MODEL)
            question = args.question.strip()
            while True:
                if question:
                    print(f"[質問] {question}\n")
                    print(ask(question, chat))
                question = input("\n次の質問 > ").strip()
                if question.lower() in {"exit", "quit"}:
                    break
    except (EOFError, KeyboardInterrupt):
        print("\n会話を終了します。")
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
