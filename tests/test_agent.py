"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import json
import sys

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent, approve_deferred_tools, main
from app import tools

BASE_TOOLS = {
    "search_glossary",
    "get_lecture_summary",
    "make_quiz",
    "save_learning_log",
    "search_materials",
}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called(monkeypatch):
    monkeypatch.setattr("app.retrieval.search", lambda *_args, **_kwargs: [])
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


def test_basic_rag_result_reaches_the_model(monkeypatch):
    hit = {"page_id": "lec02-main-p052", "lecture": 2, "page": 52, "content": "元の重みは固定"}
    monkeypatch.setattr("app.retrieval.search", lambda _query: [hit])
    model = TestModel(call_tools=["search_materials"])
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_materials"
    assert json.loads(returns[0].content)["results"] == [hit]


def test_adaptive_graph_cli_passes_short_query_and_original_question(monkeypatch, capsys):
    question = "元のユーザー質問を維持する"
    payload = {
        "results": [],
        "coverage": {"sufficient": True, "aspects": []},
        "stop_reason": "evidence_sufficient",
        "page_count": 1,
        "context_chars": 10,
        "trace": [{"event": "stopped", "reason": "evidence_sufficient"}],
    }
    calls = {}

    def fake_search(query, question=None):
        calls["query"] = query
        calls["question"] = question
        return payload

    monkeypatch.setattr(sys, "argv", ["app.agent", "--adaptive-graph", "--trace", question])
    monkeypatch.setattr("app.agent.build_model", lambda: TestModel(call_tools=["search_graph_adaptive"]))
    monkeypatch.setattr("app.retrieval.search_graph_adaptive", fake_search)

    main()

    assert calls == {"query": "a", "question": question}
    assert "evidence_sufficient" in capsys.readouterr().out


def test_graph_and_tree_modes_register_their_search_tools(monkeypatch):
    calls = []

    def search_graph(query: str) -> str:
        calls.append(("graph", query))
        return json.dumps({"seeds": [], "expanded": [], "query": query})

    def browse_tree(node_id: str | None = None) -> str:
        calls.append(("tree", node_id))
        return json.dumps({"node": {"id": node_id}, "children": []})

    monkeypatch.setattr("app.tools.search_graph", search_graph)
    monkeypatch.setattr("app.tools.browse_tree", browse_tree)
    monkeypatch.setattr("app.agent.build_model", lambda: TestModel(call_tools=["search_graph"]))
    monkeypatch.setattr(sys, "argv", ["app.agent", "--graph", "LoRAとは？"])
    main()

    monkeypatch.setattr("app.agent.build_model", lambda: TestModel(call_tools=["browse_tree"]))
    monkeypatch.setattr(sys, "argv", ["app.agent", "--tree", "LoRAとは？"])
    main()
    assert [call[0] for call in calls] == ["graph", "tree"]


def test_full_context_mode_runs_without_retrieval_tools(monkeypatch, capsys):
    model = TestModel(call_tools=[])
    monkeypatch.setattr(sys, "argv", ["app.agent", "--full-context", "LoRAとは？"])
    monkeypatch.setattr("app.agent.build_model", lambda: model)

    main()

    assert "[full-context]" in capsys.readouterr().out
    assert model.last_model_request_parameters.function_tools == []


class SaveLogTestModel(TestModel):
    def gen_tool_args(self, tool_def):
        if tool_def.name == "save_learning_log":
            return {"topic": "承認テスト", "content": "承認後に保存する"}
        return super().gen_tool_args(tool_def)


def _request_learning_log_save(log_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_PATH", log_path)
    model = SaveLogTestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("学習記録を保存して")
    assert isinstance(result.output, DeferredToolRequests)
    assert len(result.output.approvals) == 1
    return result


def _resume_with_approval(result, deferred_results):
    with agent.override(model=TestModel(call_tools=[])):
        return agent.run_sync(
            message_history=result.all_messages(),
            deferred_tool_results=deferred_results,
        )


def test_learning_log_is_not_written_before_approval(tmp_path, monkeypatch):
    log_path = tmp_path / "agent_learning_log.md"

    _request_learning_log_save(log_path, monkeypatch)

    assert not log_path.exists()


def test_learning_log_is_appended_after_approval(tmp_path, monkeypatch, capsys):
    log_path = tmp_path / "agent_learning_log.md"
    log_path.write_text("# Existing log\n", encoding="utf-8")
    result = _request_learning_log_save(log_path, monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _: "y")

    deferred_results = approve_deferred_tools(result.output)
    prompt = capsys.readouterr().out
    assert "承認テスト" in prompt
    assert "承認後に保存する" in prompt
    _resume_with_approval(result, deferred_results)

    saved = log_path.read_text(encoding="utf-8")
    assert saved.startswith("# Existing log\n")
    assert "### 学習テーマ\n承認テスト" in saved
    assert "### 学習内容\n承認後に保存する" in saved


def test_learning_log_is_not_written_when_approval_is_rejected(tmp_path, monkeypatch):
    log_path = tmp_path / "agent_learning_log.md"
    original = "# Existing log\n"
    log_path.write_text(original, encoding="utf-8")
    result = _request_learning_log_save(log_path, monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _: "n")

    deferred_results = approve_deferred_tools(result.output)
    _resume_with_approval(result, deferred_results)

    assert log_path.read_text(encoding="utf-8") == original
