"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import json

<<<<<<< HEAD
from pydantic_ai import DeferredToolRequests, DeferredToolResults
=======
from pydantic_ai import DeferredToolRequests
>>>>>>> upstream/main
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent
from app import tools

BASE_TOOLS = {"search_materials"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called(monkeypatch):
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [])
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


def test_material_result_reaches_the_model(monkeypatch):
    hit = {"page_id": "lec02-main-p052", "lecture": 2, "page": 52, "content": "元の重みは固定"}
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [hit])
    model = TestModel(call_tools=["search_materials"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
<<<<<<< HEAD
    assert returns and returns[0].tool_name == "search_glossary"


def test_save_learning_log_runs_only_after_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        pending = agent.run_sync("学習ログを保存して")

    assert isinstance(pending.output, DeferredToolRequests)
    assert len(pending.output.approvals) == 1
    assert list(tmp_path.iterdir()) == []

    request = pending.output.approvals[0]
    completed = agent.run_sync(
        None,
        model=TestModel(call_tools=[]),
        message_history=pending.all_messages(),
        deferred_tool_results=DeferredToolResults(
            approvals={request.tool_call_id: True}
        ),
    )

    saved_files = list(tmp_path.glob("*.json"))
    assert len(saved_files) == 1
    saved = json.loads(saved_files[0].read_text(encoding="utf-8"))
    assert set(saved) == {"topic", "note", "saved_at"}
    assert completed.output


def test_save_learning_log_is_skipped_when_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        pending = agent.run_sync("学習ログを保存して")

    request = pending.output.approvals[0]
    agent.run_sync(
        None,
        model=TestModel(call_tools=[]),
        message_history=pending.all_messages(),
        deferred_tool_results=DeferredToolResults(
            approvals={request.tool_call_id: False}
        ),
    )

    assert list(tmp_path.iterdir()) == []
=======
    assert returns and returns[0].tool_name == "search_materials"
    assert json.loads(returns[0].content)["results"] == [hit]
>>>>>>> upstream/main
