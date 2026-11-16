import copy
from pathlib import Path
import pytest
from app import judge, tools
from scripts.run_lec04_homework import validate

ROOT=Path(__file__).resolve().parents[1]

def test_cases_and_references():
    cases=judge.read_jsonl(ROOT/'data/eval/my_cases.jsonl')
    assert len(cases)==len({c['id'] for c in cases})==10
    ids={x['id'] for x in tools.load_glossary()}
    assert all(set(c['reference']['glossary'])<=ids for c in cases)
    assert all(c['reference']['expected'].strip() for c in cases)

def test_incomplete_labels_rejected():
    cases=judge.read_jsonl(ROOT/'data/eval/lec04_cases.jsonl')
    with pytest.raises(ValueError): validate(cases,{})
    labels={c['id']:{k:'pass' for k,_ in judge.ALL_CRITERIA} for c in cases}
    validate(cases,labels)
    cases[0]['answer']=''
    with pytest.raises(ValueError): validate(cases,labels)

def test_policy_change_and_unsure_denominator():
    cases=judge.read_jsonl(ROOT/'data/eval/lec04_cases.jsonl')
    c=next(c for c in cases if c['id']=='05')
    out=[]
    for variant in ['before','after']:
        rubric=(ROOT/f'data/eval/rubric_{variant}.md').read_text()
        agent=judge.build_judge(judge.build_test_model(),rubric)
        out.append(judge.judge_cases(agent,[c]))
    assert out[0]['05']['grounding']['verdict']=='unsure'
    assert out[1]['05']['grounding']['verdict']=='pass'
    labels={'05':{k:'pass' for k,_ in judge.ALL_CRITERIA}}
    before=judge.summarize([c],out[0],labels)
    after=judge.summarize([c],out[1],labels)
    assert before['per_criterion']['grounding']['compared']==0
    assert after['per_criterion']['grounding']['compared']==1
    assert before['coverage']['covered']==0
    assert after['coverage']['covered']==1

def test_lecture_mark_checks_last_line_only():
    assert judge.check_lecture_mark('第2回\n以上です')=='fail'
    assert judge.check_lecture_mark('説明\n関係する回：第2回\n')=='pass'

def test_generator_uses_approval_flow(monkeypatch):
    from app import agent as module
    class Result:
        output='テスト回答'
        def all_messages_json(self): return b'[]'
    calls=[]
    monkeypatch.setattr(module,'build_model',lambda:object())
    def fake(target,question,model):
        calls.append(question)
        return Result(),[{'approved':False}]
    monkeypatch.setattr(module,'run_with_approval',fake)
    rows=judge.generate_answers([{'question':'保存して'}],wait=0)
    assert calls==['保存して']
    assert rows[0]['answer']=='テスト回答'
    assert rows[0]['generation']['approvals']==[{'approved':False}]
