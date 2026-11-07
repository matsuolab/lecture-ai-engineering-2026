"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""


from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolDenied

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # save_learning_log writes into a temp dir
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")
        # tools with requires_approval stop here; approve them and resume
        if isinstance(result.output, DeferredToolRequests):
            result = _resume(result, True)

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


def _today_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()


def _resume(result, decision):
    approvals = {c.tool_call_id: decision for c in result.output.approvals}
    return agent.run_sync(
        message_history=result.all_messages(),
        deferred_tool_results=DeferredToolResults(approvals=approvals),
    )


def _saved_logs(base):
    return list((base / "learning_log").glob("*.md"))


def test_save_learning_log_requires_approval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("save this")
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert _saved_logs(tmp_path) == []


def test_save_learning_log_saves_after_approval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = _resume(agent.run_sync("save this"), True)
    assert len(_saved_logs(tmp_path)) == 1
    assert _saved_logs(tmp_path)[0].name.startswith(_today_jst() + "_")
    assert any(p.tool_name == "save_learning_log" for p in _parts(result, ToolReturnPart))
    assert isinstance(result.output, str)


def test_save_learning_log_denied_saves_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = _resume(agent.run_sync("save this"), ToolDenied("user said no"))
    assert _saved_logs(tmp_path) == []
    assert isinstance(result.output, str)


def test_save_learning_log_uses_today_not_model_date(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tools.save_learning_log("2000-01-01_tool", "x")  # a wrong date from the model is replaced
    tools.save_learning_log("quiz", "y")
    names = sorted(p.name for p in _saved_logs(tmp_path))
    today = _today_jst()
    assert names == [f"{today}_quiz.md", f"{today}_tool.md"]


def test_save_learning_log_date_is_japan_time(tmp_path, monkeypatch):
    # 2026-11-07 20:00 UTC is already 2026-11-08 in Japan
    monkeypatch.chdir(tmp_path)

    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 7, 20, 0, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(tools, "datetime", FakeDatetime)
    tools.save_learning_log("tz", "x")
    assert [p.name for p in _saved_logs(tmp_path)] == ["2026-11-08_tz.md"]
