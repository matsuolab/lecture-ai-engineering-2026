"""save_learning_log のテスト。

TestModel（偽モデル）を使い、APIを呼ばずに確かめる。
保存先は monkeypatch で一時フォルダに差し替えるので、本物の学習ログは汚れない。
"""

from datetime import date

from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent


def _log_file(tmp_path):
    return tmp_path / f"{date.today().isoformat()}.md"


def test_save_learning_log_appends_line(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    result = tools.save_learning_log("記録のテスト")
    assert "保存しました" in result
    assert _log_file(tmp_path).read_text(encoding="utf-8") == "- 記録のテスト\n"


def test_save_learning_log_waits_for_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("今日の学びを記録して")
        # 承認待ちで止まり、まだ保存されていない
        assert isinstance(result.output, DeferredToolRequests)
        assert result.output.approvals[0].tool_name == "save_learning_log"
        assert not _log_file(tmp_path).exists()

        # 承認すると保存され、最後まで完了する
        results = DeferredToolResults()
        for call in result.output.approvals:
            results.approvals[call.tool_call_id] = True
        result2 = agent.run_sync(
            message_history=result.all_messages(),
            deferred_tool_results=results,
            model=TestModel(call_tools=[]),
        )
    assert result2.output
    assert "- a" in _log_file(tmp_path).read_text(encoding="utf-8")
