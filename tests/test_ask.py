"""第1回 宿題（実装）：会話履歴のテスト（LLMもAPIキーも使わない）。

本物の genai.Client の代わりに、送られた contents を記録して決まった応答を返す
FakeClient を使う。
"""

from google.genai import errors, types

from app.ask import Conversation, chat_loop


def make_response(text: str, prompt_tokens: int = 10) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=[types.Part(text=text)])
            )
        ],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=prompt_tokens, candidates_token_count=5
        ),
    )


class FakeModels:
    def __init__(self, replies):
        # replies の要素が Exception なら、その呼び出しで送出する
        self.replies = list(replies)
        self.calls: list[list[types.Content]] = []

    def generate_content(self, *, model, contents):
        self.calls.append(list(contents))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return make_response(reply)


class FakeClient:
    def __init__(self, replies):
        self.models = FakeModels(replies)


def scripted_input(lines):
    """input() の代わりに、決まった行を順に返す関数を作る。"""
    it = iter(lines)
    return lambda _prompt: next(it)


def texts(contents: list[types.Content]) -> list[tuple[str, str]]:
    return [(c.role, c.parts[0].text) for c in contents]


def test_second_question_is_sent_with_previous_turn():
    client = FakeClient(["私はヨウヘイと覚えました。", "あなたの名前はヨウヘイです。"])
    conv = Conversation(client, model="fake")

    conv.send("私の名前はヨウヘイです。")
    answer = conv.send("私の名前は？")

    assert answer == "あなたの名前はヨウヘイです。"
    # 1回目は質問だけ、2回目は「1回目の質問・応答＋2回目の質問」を送っている
    assert texts(client.models.calls[0]) == [("user", "私の名前はヨウヘイです。")]
    assert texts(client.models.calls[1]) == [
        ("user", "私の名前はヨウヘイです。"),
        ("model", "私はヨウヘイと覚えました。"),
        ("user", "私の名前は？"),
    ]
    assert conv.turns == 2


def test_failed_call_is_not_added_to_history():
    rate_limited = errors.ClientError(
        429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}}
    )
    client = FakeClient(["一つ目の答え", rate_limited, "二つ目の答え"])
    conv = Conversation(client, model="fake")

    chat_loop(conv, input_fn=scripted_input(["一つ目", "二つ目", "二つ目（再送）", ""]))

    # 失敗したターンは履歴に残らず、再送では user と model が交互に並ぶ
    assert conv.turns == 2
    assert [c.role for c in conv.history] == ["user", "model", "user", "model"]
    assert texts(client.models.calls[2])[-1] == ("user", "二つ目（再送）")
    assert ("user", "二つ目") not in texts(client.models.calls[2])


def test_chat_loop_uses_first_question_and_stops_on_exit(capsys):
    client = FakeClient(["答え1", "答え2"])
    conv = Conversation(client, model="fake")

    chat_loop(conv, first_question="最初の質問", input_fn=scripted_input(["次の質問", "exit"]))

    assert conv.turns == 2
    assert len(client.models.calls) == 2
    out = capsys.readouterr().out
    assert "[入力トークン数] 10" in out
    assert "モデル> 答え2" in out


def test_chat_loop_stops_on_eof():
    def raise_eof(_prompt):
        raise EOFError

    conv = Conversation(FakeClient([]), model="fake")
    chat_loop(conv, input_fn=raise_eof)
    assert conv.turns == 0
