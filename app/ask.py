"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from google.genai import types
from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, history: list, temperature: float = 1.0) -> str:
    client = genai.Client(api_key=get_api_key())

    user_msg = types.Content(role="user", parts=[types.Part(text=question)])
    response = client.models.generate_content(
        model=MODEL,
        contents=history + [user_msg],
        config=types.GenerateContentConfig(temperature=temperature),
    )
    answer = response.text

    # Only save the turn once the call has succeeded
    history.append(user_msg)
    history.append(types.Content(role="model", parts=[types.Part(text=answer)]))

    usage = response.usage_metadata
    print(f"[tokens] entrée : {usage.prompt_token_count}")
    print(f"[tokens] sortie : {usage.candidates_token_count}\n")

    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--temperature", type=float, default=1.0)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[temperature] {args.temperature}")

    history: list = []
    question = args.question
    try:
        while question:
            print(f"[質問] {question}\n")
            print(ask(question, history, args.temperature))
            question = input("\nQuestion suivante (vide pour quitter) : ").strip()
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
if __name__ == "__main__":
    main()