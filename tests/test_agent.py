"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai.messages import DeferredToolRequests, ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}
APPROVAL_TOOL = "save_learning_log"


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel(call_tools=sorted(BASE_TOOLS))
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定
    assert APPROVAL_TOOL in offered

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    assert len(_parts(result, ToolReturnPart)) == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_learning_log_is_saved_only_after_approval(tmp_path, monkeypatch):
    from app import tools

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    model = TestModel(call_tools=[APPROVAL_TOOL])
    with agent.override(model=model):
        result = agent.run_sync("学習記録を保存して")

    assert isinstance(result.output, DeferredToolRequests)
    assert [call.tool_name for call in result.output.approvals] == [APPROVAL_TOOL]
    assert not (tmp_path / "learning_log").exists()

    with agent.override(model=TestModel(call_tools=[])):
        approved_result = agent.run_sync(
            message_history=result.all_messages(),
            deferred_tool_results=result.output.build_results(approve_all=True),
        )

    logs = list((tmp_path / "learning_log").glob("*.md"))
    assert len(logs) == 1
    assert logs[0].read_text(encoding="utf-8").startswith("# 学習記録\n\n")
    assert isinstance(approved_result.output, str)
