"""第1回 実装課題のテスト。Gemini APIへの通信は行わない。"""

from types import SimpleNamespace

import pytest

from app import ask as ask_module


def fake_response(message: str, prompt_tokens: int = 12, answer_tokens: int = 6):
    return SimpleNamespace(
        text=message,
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt_tokens,
            candidates_token_count=answer_tokens,
        ),
    )


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return fake_response(f"回答{len(self.questions)}")


def test_run_chat_reuses_same_session_for_multiple_questions(monkeypatch, capsys):
    chat = FakeChat()
    answers = iter(["私の名前を覚えていますか？", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    ask_module.run_chat(chat, initial_question="私の名前は太郎です。")

    assert chat.questions == ["私の名前は太郎です。", "私の名前を覚えていますか？"]
    out = capsys.readouterr().out
    assert "AI> 回答1" in out
    assert "AI> 回答2" in out
    assert "[tokens] 入力: 12 / 出力: 6" in out


def test_empty_question_is_skipped(monkeypatch):
    chat = FakeChat()
    answers = iter(["  ", "次の質問", "/quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    ask_module.run_chat(chat)

    assert chat.questions == ["次の質問"]


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt])
def test_chat_stops_gracefully_at_terminal_end(monkeypatch, exception, capsys):
    chat = FakeChat()

    def raise_end(_):
        raise exception

    monkeypatch.setattr("builtins.input", raise_end)
    ask_module.run_chat(chat)

    assert chat.questions == []
    assert "[対話終了]" in capsys.readouterr().out


def test_token_usage_handles_missing_metadata(capsys):
    ask_module.print_token_usage(SimpleNamespace(text="応答"))
    assert "利用情報なし" in capsys.readouterr().out


def test_token_usage_distinguishes_zero_from_unknown(capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=0, candidates_token_count=None)
    )
    ask_module.print_token_usage(response)
    assert "入力: 0 / 出力: 不明" in capsys.readouterr().out


def test_single_question_compatibility(monkeypatch, capsys):
    requests = []

    class FakeModels:
        def generate_content(self, *, model, contents):
            requests.append((model, contents))
            return fake_response("単発の回答")

    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: SimpleNamespace(models=FakeModels()))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-placeholder-not-a-key")

    answer = ask_module.ask("LoRAとは？")

    assert answer == "単発の回答"
    assert requests == [(ask_module.MODEL, "LoRAとは？")]
    assert "入力: 12 / 出力: 6" in capsys.readouterr().out


def test_main_chat_creates_only_one_sdk_chat(monkeypatch):
    chat = FakeChat()
    created_models = []

    class FakeChats:
        def create(self, *, model):
            created_models.append(model)
            return chat

    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: SimpleNamespace(chats=FakeChats()))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-placeholder-not-a-key")
    monkeypatch.setattr("sys.argv", ["python -m app.ask", "--chat", "質問1"])
    monkeypatch.setattr("builtins.input", lambda _: "/exit")

    ask_module.main()

    assert created_models == [ask_module.MODEL]
    assert chat.questions == ["質問1"]
