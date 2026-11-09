"""第3回 宿題（実装）: 保存の前に利用者の確認を挟むことのテスト（LLMもAPIキーも使わない）。

TestModel に save_learning_log だけを呼ばせ、
- 承認するまではファイルが書かれず、実行が DeferredToolRequests で止まること
- 承認すると保存され、拒否すると保存されずに回答が続くこと
を確かめる。
"""

import pytest
from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, run_with_approval


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    path = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", path)
    return path


def _returns(result, tool_name):
    return [
        p for m in result.all_messages() for p in m.parts
        if isinstance(p, ToolReturnPart) and p.tool_name == tool_name
    ]


def _save_model():
    return TestModel(call_tools=["save_learning_log"])


def test_save_stops_for_approval_before_writing(log_dir):
    result = agent.run_sync("今日学んだことを記録して", model=_save_model())
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert not log_dir.exists()  # 承認前なので、まだ何も書かれていない


def test_approved_save_writes_file_and_continues(log_dir):
    model = _save_model()
    first = agent.run_sync("今日学んだことを記録して", model=model)
    call = first.output.approvals[0]
    result = agent.run_sync(
        message_history=first.all_messages(),
        deferred_tool_results=DeferredToolResults(approvals={call.tool_call_id: True}),
        model=model,
    )
    assert isinstance(result.output, str)
    assert len(list(log_dir.glob("*.md"))) == 1
    assert "保存しました" in _returns(result, "save_learning_log")[0].content


def test_run_with_approval_denied_does_not_write(log_dir):
    asked = []
    result = run_with_approval(agent, "今日学んだことを記録して", _save_model(),
                               approve=lambda call: asked.append(call.tool_name) or False)
    assert asked == ["save_learning_log"]  # 利用者に1回だけ確認した
    assert isinstance(result.output, str)  # 拒否しても回答は最後まで返る
    assert not log_dir.exists()
    assert "許可しませんでした" in _returns(result, "save_learning_log")[0].content


def test_run_with_approval_approved_writes(log_dir):
    result = run_with_approval(agent, "今日学んだことを記録して", _save_model(),
                               approve=lambda call: True)
    assert isinstance(result.output, str)
    assert len(list(log_dir.glob("*.md"))) == 1
