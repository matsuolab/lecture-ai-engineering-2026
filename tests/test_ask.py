from types import SimpleNamespace

from google.genai import types

from app import ask as ask_module


def test_ask_passes_temperature_to_generate_content(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(usage_metadata=None, text="回答")

    class FakeClient:
        models = FakeModels()

    def create_client(api_key):
        assert api_key == "test-key"
        return FakeClient()

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", create_client)

    result = ask_module.ask("質問", temperature=0.2)

    assert result == "回答"
    assert calls[0]["model"] == ask_module.MODEL
    assert calls[0]["contents"] == "質問"
    assert isinstance(calls[0]["config"], types.GenerateContentConfig)
    assert calls[0]["config"].temperature == 0.2


def test_ask_omits_config_when_temperature_is_not_set(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(usage_metadata=None, text="回答")

    class FakeClient:
        models = FakeModels()

    def create_client(api_key):
        assert api_key == "test-key"
        return FakeClient()

    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(ask_module.genai, "Client", create_client)

    ask_module.ask("質問")

    assert "config" not in calls[0]
