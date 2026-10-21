"""素のLLM会話のテスト（実際のAPIは呼ばない）。"""

import app.ask as ask_module


def test_conversation_sends_history_and_prints_response_time(monkeypatch, capsys):
    class FakeModels:
        def __init__(self):
            self.calls = []
            self.answers = iter(["first answer", "second answer"])

        def generate_content(self, *, model, contents):
            self.calls.append(contents)
            return type(
                "Response",
                (),
                {"text": next(self.answers), "usage_metadata": None},
            )()

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    timestamps = iter([1.0, 2.25, 3.0, 4.5])
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: FakeClient())
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(timestamps))

    conversation = ask_module.Conversation()
    assert conversation.ask("first question") == "first answer"
    assert conversation.ask("follow-up question") == "second answer"

    calls = conversation.client.models.calls
    assert len(calls[0]) == 1
    assert [(message.role, message.parts[0].text) for message in calls[1]] == [
        ("user", "first question"),
        ("model", "first answer"),
        ("user", "follow-up question"),
    ]
    assert "[応答時間] 1.25秒" in capsys.readouterr().out
