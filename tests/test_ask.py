"""会話履歴と質問処理のテスト（外部APIを呼び出さない）。"""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from google.genai import types

from app import ask


class FakeChat:
    def __init__(self, history):
        self.history = history

    def get_history(self, curated=True):
        return self.history


def make_conversation(conversation_id, title, updated_at):
    return {
        "id": conversation_id,
        "created_at": updated_at,
        "updated_at": updated_at,
        "title": title,
        "history": [],
    }


def test_save_and_load_conversation(tmp_path, monkeypatch):
    monkeypatch.setattr(ask, "CHATS_DIR", tmp_path / "chats")
    history = [
        types.Content(role="user", parts=[types.Part(text="質問")]),
        types.Content(role="model", parts=[types.Part(text="回答")]),
    ]
    conversation = make_conversation("chat_test", "テスト", datetime.now().astimezone().isoformat())

    ask.save_conversation(conversation, FakeChat(history))
    loaded = ask.load_conversation(tmp_path / "chats" / "chat_test.json")

    assert [message.role for message in loaded["history"]] == ["user", "model"]
    assert loaded["history"][0].parts[0].text == "質問"
    assert list((tmp_path / "chats").glob("tmp*")) == []


def test_list_conversations_sorts_by_latest_update(tmp_path, monkeypatch):
    chats_dir = tmp_path / "chats"
    chats_dir.mkdir()
    monkeypatch.setattr(ask, "CHATS_DIR", chats_dir)
    now = datetime.now(timezone.utc)

    for conversation_id, title, minutes_ago in (
        ("chat_old", "古い", 2),
        ("chat_new", "新しい", 0),
        ("chat_middle", "中間", 1),
    ):
        updated = (now - timedelta(minutes=minutes_ago)).isoformat()
        (chats_dir / f"{conversation_id}.json").write_text(
            json.dumps(make_conversation(conversation_id, title, updated)),
            encoding="utf-8",
        )

    assert [item["id"] for item in ask.list_conversations()] == [
        "chat_new",
        "chat_middle",
        "chat_old",
    ]


def test_choose_conversation_by_number_id_and_latest():
    conversations = [
        {"id": "chat_new", "title": "新しい"},
        {"id": "chat_old", "title": "古い"},
    ]

    assert ask.choose_conversation(conversations, "2")["id"] == "chat_old"
    assert ask.choose_conversation(conversations, "chat_old")["id"] == "chat_old"
    assert ask.choose_conversation(conversations, "latest")["id"] == "chat_new"


def test_choose_conversation_reports_missing_selection():
    with pytest.raises(SystemExit, match="会話番号"):
        ask.choose_conversation([{"id": "chat_1"}], "3")
    with pytest.raises(SystemExit, match="会話ID"):
        ask.choose_conversation([{"id": "chat_1"}], "chat_missing")


def test_display_empty_conversation_list(capsys):
    ask.display_conversations([])

    assert "保存された会話はありません" in capsys.readouterr().out


def test_ask_handles_missing_usage_and_text(capsys):
    chat = SimpleNamespace(
        send_message=lambda question: SimpleNamespace(
            usage_metadata=None,
            text=None,
        )
    )

    answer = ask.ask("質問", chat)

    output = capsys.readouterr().out
    assert "input=unknown, output=unknown" in output
    assert answer == "（モデルからテキスト応答がありませんでした）"


def test_ask_warns_when_input_tokens_exceed_threshold(monkeypatch, capsys):
    monkeypatch.setattr(ask, "INPUT_TOKEN_WARNING_THRESHOLD", 10)
    chat = SimpleNamespace(
        send_message=lambda question: SimpleNamespace(
            usage_metadata=SimpleNamespace(
                prompt_token_count=11,
                candidates_token_count=3,
            ),
            text="回答",
        )
    )

    assert ask.ask("質問", chat) == "回答"
    output = capsys.readouterr().out
    assert "input=11, output=3" in output
    assert "[warning]" in output
