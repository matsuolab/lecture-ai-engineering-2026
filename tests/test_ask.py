from types import SimpleNamespace
import sys

from app import ask as ask_module


def test_ask_displays_token_usage_and_returns_answer(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=34),
    )
    chat = SimpleNamespace(send_message=lambda question: response)
    clock_values = iter([10.0, 11.25])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(clock_values))

    result = ask_module.ask(chat, "質問")
    output = capsys.readouterr().out

    assert result == "回答"
    assert "[応答時間] 1.25 秒" in output
    assert "入力: 12" in output
    assert "出力: 34" in output


def test_ask_handles_missing_usage_metadata(monkeypatch, capsys):
    response = SimpleNamespace(text="回答", usage_metadata=None)
    chat = SimpleNamespace(send_message=lambda question: response)

    assert ask_module.ask(chat, "質問") == "回答"
    assert "使用量を取得できませんでした" in capsys.readouterr().out


def test_main_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    responses = [
        SimpleNamespace(text="最初の回答", usage_metadata=None),
        SimpleNamespace(text="続きの回答", usage_metadata=None),
    ]
    questions = []

    class FakeChat:
        def send_message(self, question):
            questions.append(question)
            return responses[len(questions) - 1]

    chat = FakeChat()
    create_args = {}
    client = SimpleNamespace(
        chats=SimpleNamespace(
            create=lambda **kwargs: create_args.update(kwargs) or chat
        )
    )
    follow_ups = iter(["続きの質問", ""])
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask", "最初の質問"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(follow_ups))

    ask_module.main()

    assert questions == ["最初の質問", "続きの質問"]
    assert create_args["config"].temperature == 0.2
    assert "続きの回答" in capsys.readouterr().out