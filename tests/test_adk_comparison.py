"""比較ログの誤読・失敗時の提出文上書きを避けるための検証。API不要。"""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.compare_adk import parse_adk


def test_adk_jsonl_collects_tool_calls_and_responses():
    raw = '''startup message
{"content":{"parts":[{"function_call":{"name":"search_glossary","args":{"query":"LoRA"}}}]}}
{"content":{"parts":[{"function_response":{"name":"search_glossary","response":{"result":"definition"}}}]}}
{"content":{"parts":[{"text":"answer"}]}}
'''
    result = parse_adk(raw)
    assert result['calls'] == [{'name': 'search_glossary', 'args': {'query': 'LoRA'}}]
    assert result['returns'][0]['response']['result'] == 'definition'
    assert result['output'] == 'answer'
    assert result['requests'] is None


def test_adk_camel_case_and_thought_filter():
    result = parse_adk('{"content":{"parts":[{"functionCall":{"name":"get_lecture_summary","args":{"lecture":3}}}]}}\n{"content":{"parts":[{"text":"hidden","thought":true},{"text":"visible"}]}}')
    assert result['calls'][0]['args'] == {'lecture': 3}
    assert result['output'] == 'visible'


def test_no_model_answer_is_failure():
    with pytest.raises(ValueError):
        parse_adk('{"content":{"parts":[{"functionCall":{"name":"search_glossary"}}]}}')


def test_error_event_is_failure_even_without_content():
    with pytest.raises(ValueError):
        parse_adk('{"error_code":"RESOURCE_EXHAUSTED","error_message":"rate limit"}')


def test_pydantic_worker_serializes_actual_sdk_result(monkeypatch, capsys):
    import importlib
    import json
    from pydantic_ai.models.test import TestModel
    from scripts.compare_adk import pydantic_worker

    module = importlib.import_module('app.agent')
    monkeypatch.setattr(module, 'build_model', lambda: TestModel())
    pydantic_worker('SDK result serialization test')
    result = json.loads(capsys.readouterr().out)
    assert result['requests'] >= 1
    assert {c['name'] for c in result['calls']} == {'search_materials', 'make_quiz'}
    assert len(result['calls']) == len(result['returns'])


def test_missing_api_key_does_not_modify_answer():
    root = Path(__file__).resolve().parents[1]
    answer = root / 'lectures/03/answer.md'
    before = answer.read_bytes()
    env = dict(os.environ)
    env.pop('GEMINI_API_KEY', None)
    result = subprocess.run([sys.executable, 'scripts/compare_adk.py'], cwd=root,
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'GEMINI_API_KEY' in result.stderr
    assert answer.read_bytes() == before
