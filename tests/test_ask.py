from types import SimpleNamespace

from app.ask import ask, run_conversation


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        usage = SimpleNamespace(prompt_token_count=8, candidates_token_count=5)
        return SimpleNamespace(text=f"回答: {question}", usage_metadata=usage)


def test_ask_prints_latency_and_token_counts(monkeypatch, capsys):
    chat = FakeChat()
    timestamps = iter([10.0, 10.375])
    monkeypatch.setattr("app.ask.time.perf_counter", lambda: next(timestamps))

    assert ask("質問", chat) == "回答: 質問"

    output = capsys.readouterr().out
    assert "[timing] response_seconds=0.375" in output
    assert "[usage] input_tokens=8, output_tokens=5" in output


def test_follow_up_questions_reuse_chat_history(capsys):
    chat = FakeChat()
    questions = iter(["続きの質問", "exit"])

    run_conversation(chat, "最初の質問", lambda _prompt: next(questions))

    assert chat.questions == ["最初の質問", "続きの質問"]
    assert "回答: 続きの質問" in capsys.readouterr().out