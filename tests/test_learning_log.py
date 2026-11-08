"""第3回 宿題（実装）: save_learning_log と、保存の前の承認のテスト（LLMもAPIキーも使わない）。

TestModel に save_learning_log だけを呼ばせ、利用者の答え（y / n）で
保存される・されないが分かれることを確かめる。保存先は一時フォルダに差し替える。
"""

import pytest
from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, run_with_approval


@pytest.fixture(autouse=True)
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    return tmp_path / "learning_log"


def _logs(log_dir):
    return sorted(log_dir.glob("*.md")) if log_dir.exists() else []


def test_save_learning_log_appends_to_daily_file(log_dir):
    assert "保存しました" in tools.save_learning_log("LoRA", "低ランク行列だけを学習する")
    assert "保存しました" in tools.save_learning_log("QLoRA", "4bit に量子化して LoRA で学習する")
    files = _logs(log_dir)
    assert len(files) == 1  # 同じ日の記録は 1 つのファイルに追記される
    text = files[0].read_text(encoding="utf-8")
    assert "LoRA" in text and "QLoRA" in text


def test_save_learning_log_rejects_empty(log_dir):
    assert "保存していません" in tools.save_learning_log("", "本文")
    assert _logs(log_dir) == []


def test_save_learning_log_ignores_path_in_title(log_dir):
    tools.save_learning_log("../../evil", "本文")
    assert [p.name for p in log_dir.iterdir()] == [_logs(log_dir)[0].name]  # learning_log/ の外に書かない


def test_save_tool_requires_approval_and_stops_before_running(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = agent.run_sync("今日の学習を記録して")

    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert _logs(log_dir) == []  # 承認されるまでは保存されない


def test_approved_save_writes_log(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = run_with_approval(agent, "今日の学習を記録して", model, ask=lambda _: "y")

    assert isinstance(result.output, str)
    assert len(_logs(log_dir)) == 1
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    assert any(p.tool_name == "save_learning_log" and "保存しました" in str(p.content) for p in returns)


def test_fullwidth_y_counts_as_approval(log_dir):
    """日本語入力のまま答えた全角の「ｙ」でも保存される（Codespaces で実際に起きた取り違え）。"""
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        run_with_approval(agent, "今日の学習を記録して", model, ask=lambda _: "ｙ")
    assert len(_logs(log_dir)) == 1


def test_usage_counts_requests_before_and_after_approval(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        first = agent.run_sync("今日の学習を記録して")
        result = run_with_approval(agent, "今日の学習を記録して", model, ask=lambda _: "y")
    assert result.usage.requests > first.usage.requests  # 承認後の分だけでなく、前の分も含む


def test_denied_save_writes_nothing_and_tells_the_model(log_dir):
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        result = run_with_approval(agent, "今日の学習を記録して", model, ask=lambda _: "n")

    assert isinstance(result.output, str)
    assert _logs(log_dir) == []
    calls = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]
    assert [c.tool_name for c in calls] == ["save_learning_log"]
    returns = [p for m in result.all_messages() for p in m.parts if isinstance(p, ToolReturnPart)]
    assert any("断りました" in str(p.content) for p in returns)  # 断ったことがモデルに伝わる
