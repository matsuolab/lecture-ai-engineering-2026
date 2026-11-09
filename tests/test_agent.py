"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel
from pydantic_ai import DeferredToolRequests, DeferredToolResults

from app.agent import agent
from app import tools

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]




def test_base_tools_are_registered_and_called():
    model = TestModel(call_tools=list(BASE_TOOLS))
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered

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

def test_save_learning_log_is_saved_after_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])

    with agent.override(model=model):
        first = agent.run_sync("学習の記録を保存して")

        assert isinstance(first.output, DeferredToolRequests)
        assert len(first.output.approvals) == 1
        assert list(tmp_path.iterdir()) == []

        call = first.output.approvals[0]
        agent.run_sync(
            None,
            message_history=first.all_messages(),
            deferred_tool_results=DeferredToolResults(
                approvals={call.tool_call_id: True}
            ),
        )

    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].read_text(encoding="utf-8") == call.args["content"]


def test_save_learning_log_is_not_saved_when_denied(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])

    with agent.override(model=model):
        first = agent.run_sync("学習の記録を保存して")

        assert isinstance(first.output, DeferredToolRequests)
        assert len(first.output.approvals) == 1

        call = first.output.approvals[0]
        agent.run_sync(
            None,
            message_history=first.all_messages(),
            deferred_tool_results=DeferredToolResults(
                approvals={call.tool_call_id: False}
            ),
        )

    assert list(tmp_path.iterdir()) == []