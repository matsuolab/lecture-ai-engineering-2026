"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent, run_with_approvals

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
    from app import tools

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    model = TestModel(call_tools=["save_learning_log"])

    def approve_after_confirmation(prompt):
        assert "保存" in prompt
        assert not list((tmp_path / "learning_log").glob("*.txt"))
        return "y"

    monkeypatch.setattr("builtins.input", approve_after_confirmation)
    with agent.override(model=model):
        final_result = run_with_approvals(
            agent, "この内容を学習記録として保存して", model
        )

    saved_files = list((tmp_path / "learning_log").glob("*.txt"))
    assert len(saved_files) == 1
    assert saved_files[0].read_text(encoding="utf-8")
    assert final_result.output


def test_learning_log_is_not_saved_when_user_denies(tmp_path, monkeypatch):
    from app import tools

    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path / "learning_log")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = run_with_approvals(agent, "この内容を学習記録として保存して", model)

    assert result.output
    assert not list((tmp_path / "learning_log").glob("*.txt"))
