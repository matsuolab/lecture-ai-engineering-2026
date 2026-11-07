"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、指定したツールを呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import json

from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel(call_tools=["search_glossary", "get_lecture_summary"])
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

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
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])

    with agent.override(model=model):
        result = agent.run_sync("今日学んだことを記録してください")

        assert isinstance(result.output, DeferredToolRequests)
        assert len(result.output.approvals) == 1
        assert not (tmp_path / "learning_log.jsonl").exists()

        approval = DeferredToolResults(
            approvals={result.output.approvals[0].tool_call_id: True}
        )
        result = agent.run_sync(
            None,
            message_history=result.all_messages(),
            deferred_tool_results=approval,
        )

    records = [
        json.loads(line)
        for line in (tmp_path / "learning_log.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 1
    assert isinstance(records[0]["note"], str)
    assert result.output
