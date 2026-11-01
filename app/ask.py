"""第1回: 素のLLMに1回だけ質問したり、対話するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 引数を省略すると対話モード開始

対話モードでは会話履歴を保って続けて質問できます。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(response) -> None:
    # APIごとに使用量が付くとは限らないため、取得できない場合は「不明」と表示する。
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    print(
        f"[トークン] 入力: {input_tokens if input_tokens is not None else '不明'}"
        f" / 出力: {output_tokens if output_tokens is not None else '不明'}"
    )


def ask(question: str) -> str:
    # models.generate_content は単発の呼び出しなので、前後の質問との記憶は共有されない。
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    print_usage(response)
    return response.text


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    # 同じ session を使うと、送受信した会話履歴が次の質問に含まれる。
    session = client.chats.create(model=MODEL)
    print("対話モードです。「exit」「quit」で終了できます。")

    while True:
        try:
            question = input("[質問] ").strip()
        except EOFError:
            # 入力がパイプやファイルから来ていて終了した場合も、正常終了する。
            break

        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        try:
            response = session.send_message(question)
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            continue

        print_usage(response)
        print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.question is not None:
            print(f"[質問] {args.question}\n")
            print(ask(args.question))
        else:
            chat()
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
