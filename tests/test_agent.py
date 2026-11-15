"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import json

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, main, request_tool_approvals

BASE_TOOLS = {
    "search_materials",
    "make_quiz",
    "save_learning_log",
}


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
    assert json.loads(returns[0].content)["results"] == [hit]


def test_save_learning_log_waits_for_approval_and_resumes(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    first_model = TestModel(call_tools=["save_learning_log"])

    result = agent.run_sync("学習記録を保存して", model=first_model)

    assert isinstance(result.output, DeferredToolRequests)
    assert len(result.output.approvals) == 1
    assert result.output.approvals[0].tool_name == "save_learning_log"
    assert not log_dir.exists()

    monkeypatch.setattr("builtins.input", lambda _: "y")
    deferred_results = request_tool_approvals(result.output)
    assert deferred_results.approvals == {
        result.output.approvals[0].tool_call_id: True
    }

    resumed = agent.run_sync(
        None,
        model=TestModel(call_tools=[]),
        message_history=result.all_messages(),
        deferred_tool_results=deferred_results,
        usage=result.usage,
    )

    assert isinstance(resumed.output, str)
    assert len(list(log_dir.glob("*.md"))) == 1


def test_save_learning_log_is_not_written_when_declined(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    result = agent.run_sync(
        "学習記録を保存して",
        model=TestModel(call_tools=["save_learning_log"]),
    )
    assert isinstance(result.output, DeferredToolRequests)

    monkeypatch.setattr("builtins.input", lambda _: "n")
    deferred_results = request_tool_approvals(result.output)
    assert deferred_results.approvals == {
        result.output.approvals[0].tool_call_id: False
    }

    resumed = agent.run_sync(
        None,
        model=TestModel(call_tools=[]),
        message_history=result.all_messages(),
        deferred_tool_results=deferred_results,
        usage=result.usage,
    )

    assert isinstance(resumed.output, str)
    assert not log_dir.exists()


def test_cli_asks_for_approval_resumes_and_traces_save(tmp_path, monkeypatch, capsys):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", log_dir)
    model = TestModel(call_tools=["save_learning_log"])
    original_request_tool_approvals = request_tool_approvals

    def approve_then_disable_tool_calls(requests):
        deferred_results = original_request_tool_approvals(requests)
        model.call_tools = []
        return deferred_results

    monkeypatch.setattr("app.agent.build_model", lambda: model)
    monkeypatch.setattr("app.agent.request_tool_approvals", approve_then_disable_tool_calls)
    monkeypatch.setattr("builtins.input", lambda _: "y")
    monkeypatch.setattr("sys.argv", ["app.agent", "--trace", "学習記録を保存して"])

    main()

    output = capsys.readouterr().out
    assert "実行承認待ち: save_learning_log" in output
    assert "[tool call]   save_learning_log(" in output
    assert "[tool return] save_learning_log" in output
    assert "[usage]" in output
    assert len(list(log_dir.glob("*.md"))) == 1
