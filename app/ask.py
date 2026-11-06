"""会話履歴を保存・再開できる、素のLLMへの質問スクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --list
    uv run python -m app.ask --resume 2
    uv run python -m app.ask --resume

/exit または /quit で終了。会話履歴は data/chats/ に保存される。
"""

import argparse
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai.chats import Chat
from google.genai import errors, types
from pydantic import ValidationError

from app.config import MODEL, api_error_message, get_api_key

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
CHATS_DIR = Path(__file__).resolve().parent.parent / "data" / "chats"
INPUT_TOKEN_WARNING_THRESHOLD = 10_000
TITLE_MAX_LENGTH = 50


def shorten_title(title: str) -> str:
    """改行・余分な空白を整え、長いタイトルを省略する。"""
    title = " ".join(title.split())
    if len(title) > TITLE_MAX_LENGTH:
        return title[: TITLE_MAX_LENGTH - 1] + "…"
    return title


def load_conversation(path: Path) -> dict:
    """会話ファイルを読み込み、SDKで使える履歴に変換する。"""
    try:
        conversation = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"会話ファイルを読み込めません: {path}: {e}") from e

    if not isinstance(conversation, dict):
        raise SystemExit(f"会話ファイルの形式が不正です: {path}")

    for key in ("id", "updated_at", "title"):
        if not isinstance(conversation.get(key), str):
            raise SystemExit(f"会話ファイルの形式が不正です: {path}")
    if not isinstance(conversation.get("history"), list):
        raise SystemExit(f"会話ファイルの形式が不正です: {path}")

    try:
        datetime.fromisoformat(conversation["updated_at"])
        conversation["history"] = [
            types.Content.model_validate(item)
            for item in conversation["history"]
        ]
    except (ValidationError, ValueError) as e:
        raise SystemExit(f"会話履歴の形式が不正です: {path}: {e}") from e
    return conversation


def list_conversations() -> list[dict]:
    """保存済みの会話を更新日時の新しい順に返す。"""
    if not CHATS_DIR.exists():
        return []

    conversations = [
        load_conversation(path) for path in CHATS_DIR.glob("chat_*.json")
    ]
    return sorted(
        conversations,
        key=lambda item: datetime.fromisoformat(item["updated_at"]),
        reverse=True,
    )


def display_conversations(conversations: list[dict]) -> None:
    """保存済みの会話を番号付きで一覧表示する。"""
    print("保存された会話一覧")
    if not conversations:
        print("保存された会話はありません。")
        return

    for number, conversation in enumerate(conversations, start=1):
        updated = datetime.fromisoformat(
            conversation["updated_at"]
        ).astimezone().strftime("%Y-%m-%d %H:%M")
        title = shorten_title(conversation["title"])
        print(f"[{number}] {updated}  {title} ({conversation['id']})")


def create_conversation(question: str) -> dict:
    """最初の質問をタイトルにした新しい会話を作る。"""
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "id": f"chat_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}",
        "created_at": now,
        "updated_at": now,
        "title": shorten_title(question),
        "history": [],
    }


def save_conversation(conversation: dict, chat: Chat) -> None:
    """会話を一時ファイルに書き、安全に置き換える。"""
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    conversation["updated_at"] = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    conversation["history"] = [
        item.model_dump(mode="json", exclude_none=True)
        for item in chat.get_history(curated=True)
    ]

    path = CHATS_DIR / f"{conversation['id']}.json"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CHATS_DIR,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(conversation, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def choose_conversation(conversations: list[dict], selection: str) -> dict:
    """番号または会話IDで再開する会話を選ぶ。"""
    if not conversations:
        raise SystemExit("保存された会話がありません。先に会話を作成してください。")
    if selection == "latest":
        return conversations[0]
    if selection.isdecimal():
        number = int(selection)
        if 1 <= number <= len(conversations):
            return conversations[number - 1]
        raise SystemExit(f"会話番号 {number} はありません。--list で確認してください。")

    for conversation in conversations:
        if conversation["id"] == selection:
            return conversation
    raise SystemExit(f"会話IDが見つかりません: {selection}")


def ask(question: str, chat: Chat) -> str:
    response = chat.send_message(question)
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage else None
    output_tokens = usage.candidates_token_count if usage else None
    print(
        f"[tokens] input={input_tokens if input_tokens is not None else 'unknown'}, "
        f"output={output_tokens if output_tokens is not None else 'unknown'}"
    )

    if (
        input_tokens is not None
        and input_tokens > INPUT_TOKEN_WARNING_THRESHOLD
    ):
        print("[warning] 入力トークン数が10,000を超えています。")
    return response.text or "（モデルからテキスト応答がありませんでした）"


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保存して質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--list", action="store_true", help="会話一覧を表示する")
    parser.add_argument(
        "--resume",
        nargs="?",
        const="latest",
        metavar="番号または会話ID",
        help="会話を再開する（省略時は最新の会話）",
    )
    args = parser.parse_args()

    if args.list and (args.question or args.resume is not None):
        parser.error("--list は質問や --resume と同時に使えません")
    if args.resume is not None and args.question:
        parser.error("--resume と質問文は同時に使えません")

    try:
        conversations = list_conversations()
        if args.list:
            display_conversations(conversations)
            return

        if args.resume is not None:
            conversation = choose_conversation(conversations, args.resume)
        else:
            question = args.question or DEFAULT_QUESTION
            conversation = create_conversation(question)

        with genai.Client(api_key=get_api_key()) as client:
            chat = client.chats.create(
                model=MODEL,
                history=conversation["history"],
            )
            if args.resume is not None:
                print(f"[会話を再開します] {conversation['title']}")
            else:
                print(f"[model] {MODEL}")
                print(f"[質問] {question}\n")
                print(ask(question, chat))
                save_conversation(conversation, chat)

            while True:
                try:
                    question = input("\n[質問] ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if question.strip().lower() in {"/exit", "/quit"}:
                    break
                if not question.strip():
                    continue

                print()
                print(ask(question, chat))
                save_conversation(conversation, chat)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    except OSError as e:
        raise SystemExit(f"会話履歴を保存または読み込めません: {e}") from e


if __name__ == "__main__":
    main()
