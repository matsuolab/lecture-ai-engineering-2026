from types import SimpleNamespace

from app import ask


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
    )
    timestamps = iter([10.0, 12.345])

    class FakeChat:
        def send_message(self, question):
            assert question == "質問"
            return response

    monkeypatch.setattr(ask, "perf_counter", lambda: next(timestamps))

    assert ask.ask(FakeChat(), "質問") == "回答"
    assert capsys.readouterr().out == (
        "[timing] response_time_seconds=2.35\n"
        "[usage] input_tokens=12 output_tokens=34\n"
    )


def test_ask_returns_answer_when_usage_metadata_is_missing(monkeypatch, capsys):
    response = SimpleNamespace(text="回答", usage_metadata=None)
    timestamps = iter([20.0, 21.5])

    class FakeChat:
        def send_message(self, question):
            return response

    monkeypatch.setattr(ask, "perf_counter", lambda: next(timestamps))

    assert ask.ask(FakeChat(), "質問") == "回答"
    assert capsys.readouterr().out == "[timing] response_time_seconds=1.50\n"


def test_main_prompts_for_initial_question_and_keeps_chat_history(monkeypatch, capsys):
    sent_questions = []
    created_models = []

    class FakeChat:
        def send_message(self, question):
            sent_questions.append(question)
            return SimpleNamespace(text=f"回答: {question}", usage_metadata=None)

    class FakeChats:
        def create(self, *, model):
            created_models.append(model)
            return FakeChat()

    class FakeClient:
        chats = FakeChats()

        def __init__(self, *, api_key):
            assert api_key == "test-key"

    questions = iter(["最初の質問", "追加質問", ""])
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return next(questions)

    monkeypatch.setattr(ask.genai, "Client", FakeClient)
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("sys.argv", ["app.ask"])

    ask.main()

    assert created_models == [ask.MODEL]
    assert sent_questions == ["最初の質問", "追加質問"]
    output = capsys.readouterr().out
    assert "回答: 最初の質問" in output
    assert prompts == ["最初の質問: ", "\n次の質問 (空行で終了): ", "\n次の質問 (空行で終了): "]