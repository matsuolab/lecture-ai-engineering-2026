"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import json

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import RateLimits, agent, print_usage_summary, run_chat
from pydantic_ai.usage import RunUsage

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
    assert returns and returns[0].tool_name == "search_glossary"


def test_chat_passes_previous_turns_as_message_history(monkeypatch, capsys):
    prompts = iter(["最初の質問", "続きの質問", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))

    run_sync = agent.run_sync
    histories = []

    def record_history(*args, **kwargs):
        histories.append(kwargs["message_history"])
        return run_sync(*args, **kwargs)

    monkeypatch.setattr(agent, "run_sync", record_history)
    run_chat(agent, TestModel(call_tools=[]))

    assert len(histories) == 2
    assert histories[0] == []
    assert "最初の質問" in str(histories[1])
    assert capsys.readouterr().out.count("[応答時間] ") == 2


def test_usage_summary_estimates_remaining_chats_from_tightest_limit(capsys):
    print_usage_summary(
        RunUsage(requests=2, input_tokens=100, output_tokens=40),
        [],
        RateLimits(rpm=10, tpm=1000, rpd=100),
    )

    output = capsys.readouterr().out
    assert "入力: 100 tokens" in output
    assert "出力: 40 tokens" in output
    assert "[推定残り] 約4チャット" in output
    assert returns and returns[0].tool_name == "search_materials"
    assert json.loads(returns[0].content)["results"] == [hit]
