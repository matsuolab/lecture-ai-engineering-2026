"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import json
from types import SimpleNamespace

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, print_trace, run_query

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
    assert isinstance(result.output, DeferredToolRequests)
    assert [call.tool_name for call in result.output.approvals] == ["save_learning_log"]
    assert not log_dir.exists()
    assert result.output


def test_material_result_reaches_the_model(monkeypatch):
    hit = {"page_id": "lec02-main-p052", "lecture": 2, "page": 52, "content": "元の重みは固定"}
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [hit])
    model = TestModel(call_tools=["search_materials"])
    result = run_query(agent, "RAGとは？", model)
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_materials"
    assert json.loads(returns[0].content)["results"] == [hit]


def test_tree_mode_runs_with_tree_tool(monkeypatch):
    def browse_tree(node_id=None):
        return {
            "node": {"id": node_id or "root", "title": "講義", "content": "本文"},
            "children": [{"id": "lec02", "title": "第2回", "kind": "lecture"}],
        }

    monkeypatch.setattr("app.agent.browse_tree", browse_tree)
    model = TestModel(call_tools=["browse_tree"])

    result = run_query(agent, "質問", model, tree=True)

    calls = _parts(result, ToolCallPart)
    assert calls and calls[0].tool_name == "browse_tree"
    print_trace(result, elapsed_seconds=1.0)


def test_graph_mode_runs_with_graph_tool(monkeypatch):
    def search_graph(query):
        return {"seeds": [], "expanded": [], "max_hops": 2}

    monkeypatch.setattr("app.agent.search_graph", search_graph)
    model = TestModel(call_tools=["search_graph"])

    result = run_query(agent, "質問", model, graph=True)

    calls = _parts(result, ToolCallPart)
    assert calls and calls[0].tool_name == "search_graph"


def test_full_context_mode_uses_full_context_runner(monkeypatch):
    expected = object()
    received = {}

    def run_full_context(target, question, model, instructions, prompt_template):
        received.update(
            target=target,
            question=question,
            model=model,
            instructions=instructions,
            prompt_template=prompt_template,
        )
        return expected

    monkeypatch.setattr("app.agent.run_full_context", run_full_context)

    result = run_query(agent, "質問", TestModel(), full_context=True)

    assert result is expected
    assert received["target"] is agent
    assert received["question"] == "質問"
    assert "{materials}" in received["prompt_template"]


def test_full_context_mode_runs_without_tools():
    result = run_query(agent, "LoRAとは？", TestModel(), full_context=True)

    assert result.output


def test_print_trace_displays_elapsed_time(capsys):
    result = SimpleNamespace(
        all_messages=lambda: [],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5, requests=1, cost=0.001),
    )

    print_trace(result, elapsed_seconds=1.234)

    assert "[time] 回答完了まで 1.23 秒（検索・埋め込みを含む）" in capsys.readouterr().out
