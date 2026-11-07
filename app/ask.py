
import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)

    parser.add_argument(
        "--chat",
        action="store_true",
        help="会話履歴を保持して連続質問する"
    )

    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        if args.chat:
            chat(args.question)  # 会話履歴あり
        else:
            print(ask(args.question))  # 会話履歴なし

    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)

def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)
    return response.text

def chat(first_question: str) -> None:
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL) # 履歴は SDK の Chat が持つ
    question = first_question
    while question:
        response = session.send_message(question) # これまでの履歴+今回の質問を送る
        print(response.text)
        usage = response.usage_metadata
        if usage is not None:
            print(f"[tokens] 入力 {usage.prompt_token_count} / 出力 {usage.candidates_token_count}")
        question = input("\n[続けて質問(空行で終了)] ").strip()

if __name__ == "__main__":
    main()
