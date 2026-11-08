from app.ask import run_conversation


class FakeResponse:
    text = "回答"
    usage_metadata = None


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return FakeResponse()


def test_conversation_reuses_chat_until_exit(capsys):
    chat = FakeChat()
    answers = iter(["続きの質問", "exit"])

    run_conversation(chat, "最初の質問", lambda _: next(answers))

    assert chat.questions == ["最初の質問", "続きの質問"]
    assert capsys.readouterr().out.count("回答") == 2