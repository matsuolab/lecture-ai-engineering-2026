"""第1回: 素のLLMに1回だけ質問するスクリプト（Claude API 版）。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

    # モデルを切り替えるとき
    AIE_MODEL=claude-sonnet-5-5 uv run python -m app.ask "LoRAとは何ですか？"

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）

変更点（自分の fork のみ）:
    Gemini API のプロジェクトが停止されたため、Claude API で呼び出すように書き換えた。
    API キーは環境変数 ANTHROPIC_API_KEY（Codespaces secret）から読む。
    モデルは環境変数 AIE_MODEL で切り替える（未設定なら claude-haiku-5-5）。
"""

import argparse
import os

import anthropic

from app.config import api_error_message

# 既定モデル。app/config.py の既定（Gemini）は使わず、ここで Claude のモデルを決める
DEFAULT_MODEL = "claude-haiku-5-5"
MODEL = os.getenv("AIE_MODEL", DEFAULT_MODEL)

# Claude API では出力の上限トークン数の指定が必須
MAX_TOKENS = 1024

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def get_api_key() -> str:
    """環境変数 ANTHROPIC_API_KEY を返す。未設定なら手順を表示して終了する。"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit(
            "環境変数 ANTHROPIC_API_KEY が見つかりません。\n"
            "1. GitHub の Settings → Codespaces → Secrets に ANTHROPIC_API_KEY を登録し、\n"
            "   使う repository に自分の fork を選んでください。\n"
            "2. Codespaces を起動したあとに登録した場合は、Codespaces を再起動してください。\n"
            "   （左下の「Codespaces」→「Stop Current Codespace」→ 再度開く）"
        )
    return key


def ask(question: str) -> str:
    client = anthropic.Anthropic(api_key=get_api_key())
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": question}],
    )

    # 第1回 演習: 入力トークン数と出力トークン数を表示する
    usage = response.usage
    print(f"[tokens] 入力: {usage.input_tokens} / 出力: {usage.output_tokens}\n")

    # 応答は複数のブロックで返ることがあるので、テキストだけをつなげる
    return "".join(block.text for block in response.content if block.type == "text")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except anthropic.APIStatusError as e:
        print(api_error_message(e.status_code, e.message))
        raise SystemExit(1)
    except anthropic.APIConnectionError:
        print("Claude API に接続できませんでした。ネットワークを確認して再実行してください。")
        raise SystemExit(1)


if __name__ == "__main__":
    main()