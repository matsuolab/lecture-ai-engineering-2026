from unittest.mock import Mock, call, patch

import app.ask as ask_module


def test_run_chat_reuses_chat_session_for_each_question(capsys):
    client = Mock()
    chat = client.chats.create.return_value
    chat.send_message.side_effect = [
        Mock(text="answer 1", usage_metadata=None),
        Mock(text="answer 2", usage_metadata=None),
    ]

    with (
        patch.object(ask_module.genai, "Client", return_value=client),
        patch("builtins.input", side_effect=["first question", "second question", "exit"]),
    ):
        ask_module.run_chat()

    client.chats.create.assert_called_once_with(model=ask_module.MODEL)
    assert chat.send_message.call_args_list == [
        call("first question"),
        call("second question"),
    ]
    output = capsys.readouterr().out
    assert "answer 1" in output
    assert "answer 2" in output