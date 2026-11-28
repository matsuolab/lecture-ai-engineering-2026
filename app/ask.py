"""第1回: 用語集と会話履歴を使ってLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    # 2回目以降の質問を入力し、/exit で終了

用語集をシステム指示として渡し、同じチャットに質問を送って会話履歴を保持する。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import json
from pathlib import Path

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは app/glossary.json にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat(client):
    glossary_path = Path(__file__).with_name("glossary.json")
    with glossary_path.open(encoding="utf-8") as f:
        glossary = json.load(f)

    glossary_text = json.dumps(glossary, ensure_ascii=False, indent=2)
    config = types.GenerateContentConfig(
        system_instruction=(
            "あなたはAIE2026講座の質問に答えるアシスタントです。"
            "以下の用語集を根拠として回答し、用語集に情報がない場合は"
            "推測で補わず、その旨を伝えてください。\n"
            f"{glossary_text}"
        )
    )
    return client.chats.create(model=MODEL, config=config)


def ask(question: str, chat=None) -> str:
    if chat is None:
        client = genai.Client(api_key=get_api_key())
        chat = create_chat(client)

    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        client = genai.Client(api_key=get_api_key())
        chat = create_chat(client)
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(ask(question, chat))
            try:
                question = input("\n[質問] (終了: /exit): ").strip()
            except EOFError:
                break
            if question.lower() in {"/exit", "exit", "quit"}:
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
