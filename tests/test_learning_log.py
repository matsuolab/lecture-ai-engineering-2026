from datetime import datetime

import pytest

from app import tools
from app.agent import run_with_approval
from pydantic_ai.models.test import TestModel


@pytest.fixture(autouse=True)
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path)
    return tmp_path


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 1, 2, 3, 4, 5)


def test_saves_learning_log(log_dir):
    result = tools.save_learning_log("  今日学んだこと  ")

    files = list(log_dir.iterdir())
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "今日学んだこと"
    assert result == f"学習記録を保存しました: {files[0].name}"


def test_does_not_save_blank_content(log_dir):
    result = tools.save_learning_log(" \t\n ")

    assert "保存しませんでした" in result
    assert not list(log_dir.iterdir())


def test_does_not_overwrite_existing_log(log_dir, monkeypatch):
    monkeypatch.setattr(tools, "datetime", FixedDateTime)

    first_result = tools.save_learning_log("最初の記録")
    second_result = tools.save_learning_log("2番目の記録")

    files = sorted(log_dir.iterdir())
    assert len(files) == 2
    assert {path.read_text(encoding="utf-8") for path in files} == {
        "最初の記録",
        "2番目の記録",
    }
    assert first_result.endswith("20260102-030405.md")
    assert second_result.endswith("20260102-030405-1.md")


def test_content_does_not_control_log_path(log_dir):
    tools.save_learning_log("../../evil")

    files = list(log_dir.iterdir())
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "../../evil"
    assert not (log_dir.parent / "evil").exists()


def test_truncated_content_is_reported(log_dir):
    result = tools.save_learning_log("あ" * 5001)

    files = list(log_dir.iterdir())
    assert len(files) == 1
    assert len(files[0].read_text(encoding="utf-8")) == 5000
    assert "省略" in result


def test_returns_message_after_100_filename_collisions(log_dir, monkeypatch):
    monkeypatch.setattr(tools, "datetime", FixedDateTime)

    for _ in range(100):
        tools.save_learning_log("記録")

    result = tools.save_learning_log("101回目")

    assert "保存しませんでした" in result
    assert len(list(log_dir.iterdir())) == 100


@pytest.mark.parametrize("answer", ["y", "Y", "ｙ", "y"])
def test_run_with_approval_saves_when_user_approves(log_dir, monkeypatch, answer):
    from app.agent import agent

    model = TestModel(call_tools=["save_learning_log"])
    prompts = []
    original_run_sync = type(agent).run_sync

    def record_run_sync(self, user_prompt=None, **kwargs):
        prompts.append(user_prompt)
        return original_run_sync(self, user_prompt, **kwargs)

    monkeypatch.setattr(type(agent), "run_sync", record_run_sync)

    with agent.override(model=model):
        result = run_with_approval(agent, "今日の学びを残して", model, input_fn=lambda _: answer)

    files = list(log_dir.iterdir())
    assert len(files) == 1
    assert isinstance(result.output, str)
    assert prompts == ["今日の学びを残して", None]


@pytest.mark.parametrize("answer", ["n", "", "yes"])
def test_run_with_approval_does_not_save_when_user_denies(log_dir, answer):
    from app.agent import agent

    model = TestModel(call_tools=["save_learning_log"])

    with agent.override(model=model):
        result = run_with_approval(agent, "今日の学びを残して", model, input_fn=lambda _: answer)

    assert not log_dir.exists() or len(list(log_dir.iterdir())) == 0
    assert isinstance(result.output, str)


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_run_with_approval_denies_when_input_is_interrupted(log_dir, error):
    from app.agent import agent

    model = TestModel(call_tools=["save_learning_log"])

    def interrupted_input(_):
        raise error

    with agent.override(model=model):
        result = run_with_approval(agent, "今日の学びを残して", model, input_fn=interrupted_input)

    assert isinstance(result.output, str)
    assert not log_dir.exists() or len(list(log_dir.iterdir())) == 0
