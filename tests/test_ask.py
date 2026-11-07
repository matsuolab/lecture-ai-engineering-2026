"""質問スクリプトのテスト（LLMもAPIキーも使わない）。"""

from types import SimpleNamespace

import app.ask as ask_module


def test_follow_up_questions_reuse_chat_and_report_usage_and_time(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(
                text=f"回答: {question}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=5,
                ),
            )

    chat = FakeChat()

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"

            def create(model):
                assert model == ask_module.MODEL
                return chat

            self.chats = SimpleNamespace(
                create=create,
            )

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    questions = iter(["次の質問", ""])

    def read_question(prompt):
        assert "続けて質問" in prompt
        return next(questions)

    monkeypatch.setattr("builtins.input", read_question)
    monkeypatch.setattr("sys.argv", ["app.ask"])
    ticks = iter([0.0, 1.25, 2.0, 4.5])
    monkeypatch.setattr(ask_module, "perf_counter", lambda: next(ticks))

    ask_module.main()

    output = capsys.readouterr().out
    assert chat.questions == [ask_module.DEFAULT_QUESTION, "次の質問"]
    assert output.count("input_tokens=10, output_tokens=5") == 2
    assert "[応答時間] 1.25 秒" in output
    assert "[応答時間] 2.50 秒" in output
    assert output.count("回答:") == 2
