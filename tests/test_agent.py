"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # 承認が必要なツール（requires_approval=True）は、実行されずに承認待ちになるので戻り値が無い
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_save_log_waits_for_approval_and_writes_only_after_approval(tmp_path, monkeypatch):
    from app import tools

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)

    # 1回目: 承認待ちで止まり、ファイルはまだ作られない
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        result = agent.run_sync("今日の学びを記録して")
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert not list(tmp_path.glob("*.md"))

    # 2回目: 利用者が承認すると、ツールが実行されてファイルができる
    results = result.output.build_results(approvals={result.output.approvals[0].tool_call_id: True})
    with agent.override(model=TestModel(call_tools=[])):
        agent.run_sync(message_history=result.all_messages(), deferred_tool_results=results)
    assert len(list(tmp_path.glob("*.md"))) == 1


def test_denied_save_writes_nothing_and_tells_the_model(tmp_path, monkeypatch):
    from pydantic_ai import ToolDenied

    from app import tools

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        result = agent.run_sync("今日の学びを記録して")
    call_id = result.output.approvals[0].tool_call_id
    results = result.output.build_results(approvals={call_id: ToolDenied("断られた")})
    with agent.override(model=TestModel(call_tools=[])):
        result2 = agent.run_sync(message_history=result.all_messages(), deferred_tool_results=results)

    assert not list(tmp_path.glob("*.md"))
    contents = [str(p.content) for p in _parts(result2, ToolReturnPart) if p.tool_name == "save_learning_log"]
    assert contents and "断られた" in contents[0]
