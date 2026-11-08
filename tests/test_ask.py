from types import SimpleNamespace

import app.ask as ask_module


def test_ask_returns_text_and_token_counts(monkeypatch):
    response = SimpleNamespace(
        text="回答",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
    )
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: response))
    monkeypatch.setattr(ask_module.genai, "Client", lambda **_: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == ("回答", 12, 7)


def test_main_displays_input_and_output_token_counts(monkeypatch, capsys):
    # 第1回の宿題で ask は会話履歴も受け取り、main は続けて質問を待つようにしたので、
    # ask は履歴付きの呼び出しに合わせ、次の質問は空 Enter（終了）を返す
    monkeypatch.setattr(ask_module, "ask", lambda question, history=None: ("回答", 12, 7))
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")
    monkeypatch.setattr("sys.argv", ["app.ask", "質問"])

    ask_module.main()

    output = capsys.readouterr().out
    assert "入力: 12" in output
    assert "出力: 7" in output