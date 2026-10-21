"""第1回 app.ask の会話モードのテスト（LLMもAPIキーも使わない）。"""

from google.genai import chats, types

from app.ask import run_chat


class FakeModels:
    """generate_content に渡された contents を記録し、決まった回答を返す。"""

    def __init__(self):
        self.sent_contents = []

    def generate_content(self, *, model, contents, config=None):
        self.sent_contents.append(contents)
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text=f"回答{len(self.sent_contents)}")]
                    )
                )
            ]
        )


def make_chat():
    models = FakeModels()
    return models, chats.Chat(modules=models, model="fake", history=[])


def texts(contents):
    return [c.parts[0].text for c in contents]


def test_chat_keeps_history_between_turns():
    models, chat = make_chat()
    inputs = iter(["それを一言で言うと？", "exit"])
    run_chat(chat, "LoRAとは何ですか？", read_line=lambda _: next(inputs))

    assert len(models.sent_contents) == 2
    # 2回目の呼び出しには、1回目の質問と回答が含まれている
    assert texts(models.sent_contents[1]) == ["LoRAとは何ですか？", "回答1", "それを一言で言うと？"]
    assert len(chat.get_history()) == 4


def test_chat_skips_empty_input_and_ends_on_eof():
    models, chat = make_chat()
    inputs = iter(["", "  ", "質問"])

    def read_line(_):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError

    run_chat(chat, read_line=read_line)
    assert [texts(c)[-1] for c in models.sent_contents] == ["質問"]
