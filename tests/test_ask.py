from types import SimpleNamespace

from app import ask as ask_module


class FakeModels:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def generate_content(self, *, model, contents):
        self.requests.append((model, contents))
        return next(self.responses)


class FakeClient:
    def __init__(self, responses):
        self.models = FakeModels(responses)


def _response(text):
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=10,
            candidates_token_count=20,
            total_token_count=30,
        ),
    )


def test_conversation_sends_previous_user_and_model_turns():
    client = FakeClient(
        [
            _response("小学生向けの説明"),
            _response("中学生向けの説明"),
            _response("高校生向けの説明"),
        ]
    )
    history = []

    ask_module._ask_with_history(client, "小学生向けに説明して", history)
    ask_module._ask_with_history(client, "中学生向けに説明して", history)
    third = ask_module._ask_with_history(client, "高校生向けに説明して", history)

    assert third[0] == "高校生向けの説明"
    assert third[1] >= 0
    assert third[2:] == (10, 20, 30)

    sent_history = client.models.requests[2][1]
    assert [turn.role for turn in sent_history] == [
        "user",
        "model",
        "user",
        "model",
        "user",
    ]
    assert [turn.parts[0].text for turn in sent_history] == [
        "小学生向けに説明して",
        "小学生向けの説明",
        "中学生向けに説明して",
        "中学生向けの説明",
        "高校生向けに説明して",
    ]


def test_ask_remains_a_single_turn_string_api(monkeypatch):
    client = FakeClient([_response("答え")])
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "答え"
    assert client.models.requests[0][1][0].role == "user"


def test_missing_usage_metadata_is_reported_as_unavailable():
    client = FakeClient([SimpleNamespace(text="答え", usage_metadata=None)])

    answer, elapsed, input_tokens, output_tokens, total_tokens = (
        ask_module._ask_with_history(client, "質問", [])
    )

    assert answer == "答え"
    assert elapsed >= 0
    assert (input_tokens, output_tokens, total_tokens) == (None, None, None)
