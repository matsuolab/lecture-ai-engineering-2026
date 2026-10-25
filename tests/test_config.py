import pytest

from app.config import get_api_key


def test_get_api_key_returns_ascii_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyExampleKey123")

    assert get_api_key() == "AIzaSyExampleKey123"


def test_get_api_key_rejects_non_ascii_characters(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clé")

    with pytest.raises(SystemExit, match="ASCII 以外"):
        get_api_key()
