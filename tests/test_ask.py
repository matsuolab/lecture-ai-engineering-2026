from types import SimpleNamespace

import pytest

from app import ask as ask_module


def test_main_repeats_question_with_temperature(monkeypatch, capsys):
    requests = []

    class FakeModels:
        def generate_content(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(text=f"answer {len(requests)}", usage_metadata=None)

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.models = FakeModels()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        "sys.argv",
        ["app.ask", "--temperature", "0.7", "same question"],
    )

    ask_module.main()

    assert len(requests) == 3
    assert all(request["model"] == ask_module.MODEL for request in requests)
    assert all(request["contents"] == "same question" for request in requests)
    assert all(
        request["config"].temperature == 0.7
        for request in requests
    )
    output = capsys.readouterr().out
    assert "[回答 1/3]" in output
    assert "[回答 2/3]" in output
    assert "[回答 3/3]" in output
    assert "answer 1" in output
    assert "answer 3" in output


@pytest.mark.parametrize("repeat", ["0", "-1", "not-a-number"])
def test_repeat_must_be_positive_integer(monkeypatch, repeat):
    monkeypatch.setattr("sys.argv", ["app.ask", "--repeat", repeat])

    with pytest.raises(SystemExit) as exc_info:
        ask_module.main()

    assert exc_info.value.code == 2
