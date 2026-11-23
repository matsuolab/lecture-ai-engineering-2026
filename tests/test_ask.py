from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    request = {}
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
    )

    def generate_content(**kwargs):
        request.update(kwargs)
        return response

    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(
            models=SimpleNamespace(generate_content=generate_content)
        ),
    )

    assert ask_module.ask("質問") == "回答"
    assert request["config"] == {"temperature": 0.2}
    output = capsys.readouterr().out
    assert "[temperature] 0.2" in output
    assert "[usage] 入力トークン数: 12, 出力トークン数: 7" in output
    assert "[time] 応答時間:" in output


def test_ask_handles_missing_usage_metadata(monkeypatch, capsys):
    response = SimpleNamespace(text="回答", usage_metadata=None)
    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        lambda **kwargs: SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **kwargs: response)
        ),
    )

    assert ask_module.ask("質問") == "回答"
    assert "[usage] 入力トークン数: 不明, 出力トークン数: 不明" in capsys.readouterr().out


def test_compare_sends_each_question_to_every_model(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ask_module,
        "ask",
        lambda question, model, temperature: calls.append(
            (question, model, temperature)
        ) or f"{model}の回答",
    )

    ask_module.compare(["質問1", "質問2"], ["model-a", "model-b"], [0.2, 1.0])

    assert calls == [
        ("質問1", "model-a", 0.2),
        ("質問1", "model-a", 1.0),
        ("質問1", "model-b", 0.2),
        ("質問1", "model-b", 1.0),
        ("質問2", "model-a", 0.2),
        ("質問2", "model-a", 1.0),
        ("質問2", "model-b", 0.2),
        ("質問2", "model-b", 1.0),
    ]


def test_interactive_keeps_history_per_model(monkeypatch, capsys):
    histories = {}

    class FakeChat:
        def __init__(self, model, temperature):
            self.model = model
            self.temperature = temperature
            self.messages = []
            histories[(model, temperature)] = self.messages

        def send_message(self, message):
            self.messages.append(message)
            return SimpleNamespace(
                text=f"{self.model}/{self.temperature}の回答",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=3, candidates_token_count=4
                ),
            )

    class FakeClient:
        class Chats:
            @staticmethod
            def create(model, config):
                return FakeChat(model, config["temperature"])

        chats = Chats()

    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    inputs = iter(["最初の質問", "続きの質問", "/exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    ask_module.interactive(["model-a", "model-b"], [0.2, 1.0])

    assert histories == {
        ("model-a", 0.2): ["最初の質問", "続きの質問"],
        ("model-a", 1.0): ["最初の質問", "続きの質問"],
        ("model-b", 0.2): ["最初の質問", "続きの質問"],
        ("model-b", 1.0): ["最初の質問", "続きの質問"],
    }
    output = capsys.readouterr().out
    assert "model-a/0.2の回答" in output
    assert "model-b/1.0の回答" in output