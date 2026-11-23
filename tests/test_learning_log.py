import pytest
from pydantic_ai import DeferredToolRequests
from pydantic_ai.models.test import TestModel
from app import tools
from app.agent import build_agent, run_with_approval, LEC03_INSTRUCTIONS as INSTRUCTIONS, SEARCH_RULE

@pytest.mark.parametrize('answer, count', [('y', 1), ('n', 0), ('', 0)])
def test_approval_boundary(tmp_path, monkeypatch, answer, count):
    dest = tmp_path / 'learning_log'
    monkeypatch.setattr(tools, 'LEARNING_LOG_DIR', dest)
    def decide(prompt):
        assert not dest.exists()
        return answer
    result, decisions = run_with_approval(build_agent('implementation'), '保存して',
        TestModel(call_tools=['save_learning_log']), decide)
    assert not isinstance(result.output, DeferredToolRequests)
    assert len(list(dest.glob('*.md'))) == count
    assert decisions[0]['approved'] == bool(count)


def test_eof_denies(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, 'LEARNING_LOG_DIR', tmp_path / 'log')
    def eof(prompt):
        raise EOFError
    _, decisions = run_with_approval(build_agent('implementation'), '保存',
                                    TestModel(call_tools=['save_learning_log']), eof)
    assert decisions[0]['approved'] is False
    assert not (tmp_path / 'log').exists()


def test_save_content_and_unique_name(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, 'LEARNING_LOG_DIR', tmp_path)
    tools.save_learning_log('../タイトル', '日本語の学習メモ')
    tools.save_learning_log('../タイトル', '2回目')
    files = list(tmp_path.glob('*.md'))
    assert len(files) == 2
    assert any('日本語の学習メモ' in p.read_text() for p in files)


def test_empty_note_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, 'LEARNING_LOG_DIR', tmp_path / 'log')
    with pytest.raises(ValueError):
        tools.save_learning_log(' ', '本文')
    assert not (tmp_path / 'log').exists()


def test_basic_changes_exactly_one_line():
    assert INSTRUCTIONS.count(SEARCH_RULE) == 1
    assert len(INSTRUCTIONS.splitlines()) - len(INSTRUCTIONS.replace(SEARCH_RULE, '').splitlines()) == 1
