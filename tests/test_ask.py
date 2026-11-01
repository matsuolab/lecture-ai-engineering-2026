from types import SimpleNamespace

from app import ask


def test_chat_loop_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(text=f"回答: {question}", usage_metadata=None)

    questions = iter(["LoRAとは？", "それの利点は？", "/quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))
    chat = FakeChat()

    ask.chat_loop(chat)

    assert chat.questions == ["LoRAとは？", "それの利点は？"]
    assert "回答: LoRAとは？" in capsys.readouterr().out


def test_chat_loop_sends_initial_question_before_follow_ups(monkeypatch):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(text="回答", usage_metadata=None)

    monkeypatch.setattr("builtins.input", lambda _: "/exit")
    chat = FakeChat()

    ask.chat_loop(chat, "最初の質問")

    assert chat.questions == ["最初の質問"]
