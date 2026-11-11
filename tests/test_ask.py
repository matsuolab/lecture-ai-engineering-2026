from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
        text="回答",
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert "[tokens] 入力: 12, 出力: 7" in capsys.readouterr().out


def test_ask_handles_missing_usage_metadata(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="回答")
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert "[tokens] 入力: 不明, 出力: 不明" in capsys.readouterr().out


def test_run_chat_sends_follow_up_questions_to_the_same_chat(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=2),
        text="回答",
    )

    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return response

    chat = FakeChat()
    questions = iter(["続けて質問", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.run_chat(chat, first_question="最初の質問")

    assert chat.questions == ["最初の質問", "続けて質問"]
    assert capsys.readouterr().out.count("回答") == 2