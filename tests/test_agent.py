"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import INSTRUCTIONS, _resolve_deferred_tool_requests, agent

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


def _deferred_save_request():
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        return agent.run_sync(
            "第2回の重要用語を3つ教えて。そして、その説明内容を学習ログファイルに保存してください"
        )


def test_explicit_save_requests_must_use_learning_log_tool():
    assert "保存を明示的に依頼したら、回答を終える前に必ず save_learning_log" in INSTRUCTIONS
    assert "複数の用語を尋ねられた場合はすべての説明" in INSTRUCTIONS


def test_save_learning_log_waits_for_cli_approval(monkeypatch, tmp_path):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    result = _deferred_save_request()

    assert isinstance(result.output, DeferredToolRequests)
    assert result.output.approvals

    with agent.override(model=TestModel(call_tools=[])):
        result = _resolve_deferred_tool_requests(agent, result, TestModel(call_tools=[]))

    assert result.output
    assert not log_dir.exists()


def test_save_learning_log_runs_after_cli_approval(monkeypatch, tmp_path):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    result = _deferred_save_request()

    with agent.override(model=TestModel(call_tools=[])):
        result = _resolve_deferred_tool_requests(agent, result, TestModel(call_tools=[]))

    assert "保存しました" in result.output
    assert list(log_dir.glob("*.jsonl"))
