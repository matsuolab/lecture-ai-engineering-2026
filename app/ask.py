"""Lecture 1: ask a raw LLM, keeping conversation history for follow-up questions.

Usage:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # omit the question to use the course-specific default

In a terminal, you can keep asking after the first answer.
Empty line, quit, or exit stops. Piped or scripted runs ask once and exit.

This is a raw call with no tools. Course-specific questions may get "I don't know"
or a plausible generic answer that does not match the course.
(Lecture 3 adds a glossary-searching agent.)
"""

import argparse
import sys

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# Course-specific question. The correct answer is homework-levels in data/glossary.json
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def _print_usage(response) -> None:
    usage = response.usage_metadata
    if usage is not None:
        print(f"[tokens] input={usage.prompt_token_count} / output={usage.candidates_token_count}")


def ask(question: str, history: list | None = None, client: genai.Client | None = None) -> str:
    """Ask once and append the user/model turn to history when it is provided."""
    if client is None:
        client = genai.Client(api_key=get_api_key())
    if history is None:
        history = []

    history.append({"role": "user", "parts": [{"text": question}]})
    response = client.models.generate_content(model=MODEL, contents=history)
    _print_usage(response)

    text = response.text or ""
    history.append({"role": "model", "parts": [{"text": text}]})
    return text


def _follow_up_loop(client: genai.Client, history: list) -> None:
    print("\nYou can ask follow-up questions (empty line / quit / exit to stop)")
    while True:
        try:
            follow_up = input("Question> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if follow_up.lower() in ("", "q", "quit", "exit"):
            return
        print(f"[question] {follow_up}\n")
        print(ask(follow_up, history=history, client=client))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a raw LLM (keeps history so you can ask follow-ups)"
    )
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[question] {args.question}\n")

    client = genai.Client(api_key=get_api_key())
    history: list = []
    try:
        print(ask(args.question, history=history, client=client))
        if sys.stdin.isatty():
            _follow_up_loop(client, history)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
