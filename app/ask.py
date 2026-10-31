"""第1回: 素のLLMと対話するスクリプト。

使い方:
    uv run python -m app.ask
    uv run python -m app.ask --temperature 0.7

temperature のデフォルトは 2.0。会話履歴は chat_history.json に保存する。
ツールを持たない「素の」LLMの応答を確認しよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import json
import time
from pathlib import Path
from google import genai
from google.genai import errors, types
from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
#add lec1 
DEFAULT_TEMPERATURE = 2.0
HISTORY_FILE = Path(__file__).with_name("chat_history.json")

def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(temperature=DEFAULT_TEMPERATURE))

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    print(f"[入力トークン数] {input_tokens if input_tokens is not None else '不明'}")
    print(f"[出力トークン数] {output_tokens if output_tokens is not None else '不明'}")

    return response.text

#add 履歴に基づいた繰り返し質問＋出力結果のファイル書き出し
def chat(temperature: float) -> None:
    client = genai.Client(api_key=get_api_key())

    history = json.loads(HISTORY_FILE.read_text(encoding="utf-8")) if HISTORY_FILE.exists() else []
    session = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(temperature=temperature),
        history=history,
    )

    while True:
        question = input("質問（終了するには exit）> ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        print(f"[質問] {question}")
        start_time = time.perf_counter()
        response = session.send_message(question)
        elapsed_time = time.perf_counter() - start_time
        print(response.text)

        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage is not None else None
        output_tokens = usage.candidates_token_count if usage is not None else None
        print(f"[応答時間] {elapsed_time:.2f}秒")
        print(f"[入力トークン数] {input_tokens if input_tokens is not None else '不明'}")
        print(f"[出力トークン数] {output_tokens if output_tokens is not None else '不明'}")

        history = [
            item.model_dump(mode="json", exclude_none=True)
            for item in session.get_history()
        ]
        HISTORY_FILE.write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMと対話する")
    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"回答のランダム性（デフォルト: {DEFAULT_TEMPERATURE}）",
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[temperature] {args.temperature}")
    try:
        chat(args.temperature)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
