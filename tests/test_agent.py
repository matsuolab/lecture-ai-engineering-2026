"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, confirm_tool_approvals

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


def test_learning_log_is_deferred_until_approved(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("学習記録を保存して")

    assert isinstance(result.output, DeferredToolRequests)
    assert [call.tool_name for call in result.output.approvals] == ["save_learning_log"]
    assert not tools.LOG_DIR.exists()


def test_rejecting_learning_log_returns_denial(monkeypatch, tmp_path):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("学習記録を保存して")

    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert isinstance(result.output, DeferredToolRequests)
    denied = confirm_tool_approvals(result.output)
    assert denied.approvals == {
        result.output.approvals[0].tool_call_id: False
    }

    with agent.override(model=TestModel(call_tools=[])):
        final = agent.run_sync(
            message_history=result.all_messages(),
            deferred_tool_results=denied,
        )
    assert isinstance(final.output, str)
    assert not tools.LOG_DIR.exists()


def test_approving_learning_log_saves_record(monkeypatch, tmp_path):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LOG_DIR", log_dir)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("学習記録を保存して")

    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert isinstance(result.output, DeferredToolRequests)
    approved = confirm_tool_approvals(result.output)
    with agent.override(model=TestModel(call_tools=[])):
        final = agent.run_sync(
            message_history=result.all_messages(),
            deferred_tool_results=approved,
        )

    assert isinstance(final.output, str)
    files = list(log_dir.glob("*.json"))
    assert len(files) == 1
