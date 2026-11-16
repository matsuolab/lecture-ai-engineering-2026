from types import SimpleNamespace

from app.ask import run_chat


def test_chat_reuses_session_for_follow_up_questions(monkeypatch):
    sent = []

    class FakeChat:
        def send_message(self, message):
            sent.append(message)
            return SimpleNamespace(text=f"回答: {message}")

    questions = iter(["続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    run_chat(FakeChat(), "最初の質問")

    assert sent == ["最初の質問", "続きの質問"]