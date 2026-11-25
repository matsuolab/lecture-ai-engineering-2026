"""第6回 宿題（基礎・実装）：MCP サーバーに足したツールのテスト。LLM も API キーも使わない。

- 範囲外の引数は、何がいけないか・次に何を指定すればよいかが分かる文になる
- 用語集サーバーを実際に起動し（stdio）、足したツールが MCP 経由で一覧に出る
- 範囲外のメッセージが、知らせ方（return / raise / ToolError）によってモデルにどう届くか
"""

import json
import random

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

from app import tools
from app.mcp_agent import build_mcp_agent

QUIZ_TOOL = "glossary_make_quiz"


def _config(tmp_path, quiz_errors: str = "return"):
    """glossary サーバーだけを、指定した知らせ方で起動する設定ファイル。"""
    args = ["run", "python", "-m", "app.mcp_server"]
    if quiz_errors != "return":
        args += ["--quiz-errors", quiz_errors]
    path = tmp_path / f"mcp_{quiz_errors}.json"
    path.write_text(json.dumps({"mcpServers": {"glossary": {"command": "uv", "args": args}}}), encoding="utf-8")
    return path


# ------------------------------------------------------------------ 関数そのもの（MCP なし）

def test_quiz_for_a_lecture_in_the_glossary():
    data = json.loads(tools.make_quiz(2, count=3))
    assert data["lecture"] == 2 and len(data["quizzes"]) == 3
    second = {e["term"]: e["definition"] for e in tools.load_glossary() if e["lecture"] == 2}
    for quiz in data["quizzes"]:
        term = quiz["question"].removeprefix("「").removesuffix("」の意味は？")
        assert second[term] == quiz["answer"]  # 第2回の用語と、その定義が答えになる
    assert len({q["question"] for q in data["quizzes"]}) == 3  # 同じ問題を重ねない


def test_build_quiz_can_be_reproduced_with_a_seed():
    a = tools.build_quiz(1, 2, rng=random.Random(0))
    b = tools.build_quiz(1, 2, rng=random.Random(0))
    assert a == b


@pytest.mark.parametrize(
    ("lecture", "count", "expected"),
    [
        (99, 1, "第99回はこの講座にありません。この講座は第1〜13回です"),
        (0, 1, "第0回はこの講座にありません"),
        (-1, 1, "第-1回はこの講座にありません"),
        (5, 1, "第5回の用語はまだ用語集にありません"),
        (2, 0, "問題数 count は1〜5で指定してください（指定された値: 0）"),
        (2, 10, "問題数 count は1〜5で指定してください（指定された値: 10）"),
    ],
)
def test_out_of_range_returns_a_message_with_next_steps(lecture, count, expected):
    message = tools.make_quiz(lecture, count)
    assert message.startswith("クイズを作れません: ") and expected in message
    if "count" not in expected:
        assert "クイズを作れる回: 第1回（26語）、第2回（12語）" in message  # 次に指定できる回も示す
    with pytest.raises(tools.QuizArgumentError, match=expected):
        tools.build_quiz(lecture, count)


# ------------------------------------------------------------------ MCP 経由

def test_basic_and_quiz_tools_are_published_without_changing_the_agent(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_config(tmp_path)).run_sync("ツール一覧", model=model)
    offered = {t.name: t for t in model.last_model_request_parameters.function_tools}
    assert {"glossary_search_glossary", "glossary_get_lecture_summary", QUIZ_TOOL} <= set(offered)
    params = offered[QUIZ_TOOL].parameters_json_schema["properties"]
    assert params["lecture"]["type"] == "integer" and params["count"]["default"] == 1


def _run_out_of_range(tmp_path, quiz_errors: str, calls: int):
    """モデルの代わりに、make_quiz(lecture=99) を calls 回呼んでから答える偽モデルで実行する。"""
    seen = []

    def model_fn(messages, info: AgentInfo):
        seen.extend(p for p in messages[-1].parts if isinstance(p, (ToolReturnPart, RetryPromptPart)))
        if len(seen) < calls:
            return ModelResponse(parts=[ToolCallPart(QUIZ_TOOL, {"lecture": 99})])
        return ModelResponse(parts=[TextPart("第99回はありません")])

    agent = build_mcp_agent(_config(tmp_path, quiz_errors))
    with capture_run_messages():
        try:
            output = agent.run_sync("第99回のクイズを作って", model=FunctionModel(model_fn)).output
        except UnexpectedModelBehavior as e:
            output = e
    return seen, output


def test_returned_message_reaches_the_model_as_a_normal_result(tmp_path):
    seen, output = _run_out_of_range(tmp_path, "return", calls=2)
    assert [type(p) for p in seen] == [ToolReturnPart, ToolReturnPart]
    assert "この講座は第1〜13回です" in str(seen[0].content)
    assert output == "第99回はありません"  # 同じ呼び出しを繰り返しても、実行は止まらない


def test_plain_exception_hides_the_message_from_the_model(tmp_path):
    seen, output = _run_out_of_range(tmp_path, "raise", calls=1)
    prompt = seen[0].model_response()
    assert isinstance(seen[0], RetryPromptPart)
    assert "Error executing tool make_quiz" in prompt and "第1〜13回" not in prompt  # 理由が届かない
    assert "Fix the errors and try again." in prompt


def test_tool_error_passes_the_message_as_a_retry_prompt(tmp_path):
    seen, _ = _run_out_of_range(tmp_path, "tool-error", calls=1)
    assert isinstance(seen[0], RetryPromptPart)
    assert "この講座は第1〜13回です" in seen[0].model_response()


def test_repeating_a_failed_call_stops_the_run_when_raised(tmp_path):
    # 例外で知らせると「やり直し」の扱いになり、同じ呼び出しを繰り返すと実行全体が止まる
    _, output = _run_out_of_range(tmp_path, "tool-error", calls=2)
    assert isinstance(output, UnexpectedModelBehavior)
    assert "exceeded max retries" in str(output)
