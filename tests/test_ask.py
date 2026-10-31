from types import SimpleNamespace
import sys

import app.ask as ask_module


def test_interactive_chat_reuses_chat_session(monkeypatch, capsys):
    sent_questions = []
    chat_options = {}

    class FakeChat:
        def send_message(self, question):
            sent_questions.append(question)
            return SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=5,
                ),
                text=f"reply {len(sent_questions)}",
            )

    chat = FakeChat()
    client = SimpleNamespace(
        chats=SimpleNamespace(create=lambda **kwargs: chat_options.update(kwargs) or chat),
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test")
    questions = iter(["first", "follow-up", ":q"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive", "--model", "gemini-3.5-flash"])
    elapsed_values = iter([10.0, 10.25, 20.0, 20.75])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(elapsed_values))

    ask_module.main()

    output = capsys.readouterr().out
    assert chat_options == {"model": "gemini-3.5-flash"}
    assert sent_questions == ["first", "follow-up"]
    assert "reply 1" in output
    assert "reply 2" in output
    assert output.count("[response time] 0.25 s") == 1
    assert output.count("[response time] 0.75 s") == 1
    assert output.index("reply 1") < output.index("[response time] 0.25 s")
    assert output.index("reply 2") < output.index("[response time] 0.75 s")


def test_main_passes_selected_model_to_single_question(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(sys, "argv", ["app.ask", "--model", "gemini-3.5-flash", "LoRAとは？"])
    monkeypatch.setattr(ask_module, "ask", lambda question, model: calls.append((question, model)) or "answer")
    elapsed_values = iter([2.0, 3.5])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(elapsed_values))

    ask_module.main()

    assert calls == [("LoRAとは？", "gemini-3.5-flash")]
    output = capsys.readouterr().out
    assert "[model] gemini-3.5-flash" in output
    assert output.index("answer") < output.index("[response time] 1.50 s")