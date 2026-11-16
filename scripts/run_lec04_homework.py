"""基礎・実装の実行補助。実測前の結果や人手ラベルを作らない。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import judge

BASE = ROOT / 'lectures/04'
RESULTS = BASE / 'results'
MY = ROOT / 'data/eval/my_cases.jsonl'

def validate(cases, labels):
    ids = [c['id'] for c in cases]
    if len(ids) != 10 or len(set(ids)) != 10:
        raise ValueError('評価セットは重複のない10件にしてください')
    if set(labels) != set(ids):
        raise ValueError('10件すべてラベル付けしてください。別の評価セットのラベルは使えません')
    for c in cases:
        if not c.get('answer', '').strip():
            raise ValueError('先に回答を生成してください')
        if any(labels[c['id']].get(k) not in ('pass', 'fail') for k, _ in judge.ALL_CRITERIA):
            raise ValueError('5基準すべてに合格/不合格を付けてください')

def label(kind):
    cases_path = MY if kind == 'my' else judge.DEFAULT_CASES
    labels_path = BASE / ('my_labels.jsonl' if kind == 'my' else 'labels.jsonl')
    cases = judge.read_jsonl(cases_path)
    labels = judge.load_labels(labels_path) if labels_path.exists() else {}
    for c in cases:
        if c['id'] in labels:
            continue
        if not c.get('answer', '').strip():
            raise SystemExit('回答が未生成です。先に generate を実行してください')
        print(f"\n=== {c['id']} / {c['category']} ===\n質問: {c['question']}\n回答:\n{c['answer']}\n{judge.reference_text(c)}")
        row = {'id': c['id']}
        for k, name in judge.ALL_CRITERIA:
            while True:
                v = input(f'{name}：合格 y / 不合格 n > ').strip().lower()
                if v in ('y', 'n'):
                    row[k] = 'pass' if v == 'y' else 'fail'
                    break
        row['unsure_flag'] = input('判断に迷った？ y / n > ').strip().lower() == 'y'
        row['note'] = input('理由・メモ（空欄でも可）> ').strip()
        row['label_source'] = 'user_interactive'
        labels[c['id']] = row
        judge.write_jsonl(labels_path, list(labels.values()))
    print(f'保存完了: {labels_path}')

def grade(model=None):
    tasks = [('basic_before', judge.DEFAULT_CASES, BASE/'labels.jsonl', ROOT/'data/eval/rubric_before.md'),
             ('basic_after', judge.DEFAULT_CASES, BASE/'labels.jsonl', ROOT/'data/eval/rubric_after.md'),
             ('implementation', MY, BASE/'my_labels.jsonl', ROOT/'data/eval/rubric_after.md')]
    # APIを呼ぶ前に3条件を検証
    for _, c, l, _ in tasks:
        validate(judge.read_jsonl(c), judge.load_labels(l))
    outdir = BASE/'smoke_results' if model == 'test' else RESULTS
    outdir.mkdir(parents=True, exist_ok=True)
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for _, c, l, r in tasks for p in (c,l,r)}
    manifest = outdir/'inputs_sha256.json'
    if manifest.exists() and json.loads(manifest.read_text()) != inputs:
        raise SystemExit('前回から入力が変わっています。resultsを別名で保存して新しい実験を開始してください')
    if not manifest.exists():
        manifest.write_text(json.dumps(inputs,indent=2),encoding='utf-8')
    # 比較時点の入力を固定し、同じラベルと回答を両条件で使う
    for rel in inputs:
        dest = outdir/'inputs'/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT/rel).read_bytes())
    from app.config import MODEL
    for name,c,l,r in tasks:
        target = outdir/f'{name}.json'
        if target.exists():
            previous = json.loads(target.read_text())
            if previous['model'] != (model or MODEL):
                raise SystemExit('前回とモデルが異なります')
            print(f'保存済みの条件を再利用: {name}')
            continue
        cmd = [sys.executable,'-m','app.judge','--cases',str(outdir/'inputs'/c.relative_to(ROOT)),
               '--labels',str(outdir/'inputs'/l.relative_to(ROOT)), '--rubric',str(outdir/'inputs'/r.relative_to(ROOT)),
               '--out',str(outdir/f'{name}.json'),'--wait','0' if model == 'test' else '2']
        if model: cmd += ['--model',model]
        subprocess.run(cmd, cwd=ROOT, check=True)
    (outdir/'inputs_sha256.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
    if model != 'test': report()

def report():
    names = ['basic_before','basic_after','implementation']
    runs = [json.loads((RESULTS/f'{n}.json').read_text()) for n in names]
    if any(r['model']=='test' for r in runs):
        raise SystemExit('偽モデルの結果は提出用レポートにしません')
    if runs[0]['model'] != runs[1]['model']:
        raise SystemExit('基礎のモデルが異なります。基準文言だけを変えてください')
    lines = ['# 第4回 宿題レポート案','', '## 宿題','',
             '- 取り組んだレベル：基礎・実装',
             '- AI利用：コードと作問案の作成にAIを利用。人手ラベルは本人が回答と参照を読んで入力。',
             '- 基礎：同じ回答・同じ人手ラベルで、用語集にない語の一般説明を許容する方針だけを採点基準に追加。モデル・判定順は固定。',
             '- 実装：作問モードと同じJSONL形式で10問を作成。正常系・表記ゆれ・複数用語・誤った前提・未知語・宿題の完成解答・講座外・役割変更・情報不足・存在しない回を含む。',
             '', '| 基準 | 基礎・前 | 基礎・後 | 実装 |','|---|---|---|---|']
    for k,n in judge.ALL_CRITERIA:
        vals=[]
        for r in runs:
            p=r['summary']['per_criterion'][k]
            vals.append(f"{p['agree']}/{p['compared']}（比較対象 {p['compared']}/{p['total']}）")
        lines.append('| '+n+' | '+' | '.join(vals)+' |')
    for label,fn in [('要確認の項目数',lambda s:len(s['review'])),('要確認を含む質問数',lambda s:len({v['id'] for v in s['review']})),('総合の自動判定対象',lambda s:f"{s['coverage']['covered']}/{s['coverage']['total']}")]:
        lines.append('| '+label+' | '+' | '.join(str(fn(r['summary'])) for r in runs)+' |')
    lines += ['', '### 判定の分担と考察','',
              '末尾の「第N回」の有無は、再現可能な文字列検査に任せる。ただし、表示された回が内容的に正しいかは正規表現だけでは判断できない。根拠との整合性、範囲外への対応、完成解答とヒントの境界、説明の読みやすさは文脈を要するためLLMで判定し、unsureと人との不一致を人が再確認する。',
              '一致率はunsureを除いた分母で計算されるため、要確認数とcoverageを併記する。10問・各条件1回のため、一般的な性能や変更の因果効果を断定しない。',
              '', '### 実測の不一致・要確認']
    for name,r in zip(names,runs):
        lines += ['',f"#### {name}（{r['model']} / {r['run_at']}）"]
        for m in r['summary']['mismatches']:
            lines.append(f"- {m['id']} / {m['name']}：人={m['human']}、採点器={m['judge']}。理由：{m['reason']}")
        for m in r['summary']['review']:
            lines.append(f"- 要確認 {m['id']} / {m['name']}：{m['reason']}")
    lines += ['', '### 本人の確認（提出前に追記）', '- 不一致の中で納得した／納得しなかった項目と理由：未記入', '- 実際に難しかった点・学んだこと：未記入', '', '※このファイルは実測から作った下書き。確認後にanswer.mdの宿題欄へ反映する。']
    (BASE/'homework_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with zipfile.ZipFile(ROOT/'lec04_results.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(RESULTS.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(ROOT))
        for p in [BASE/'homework_report.md', MY, BASE/'labels.jsonl', BASE/'my_labels.jsonl']:
            z.write(p,p.relative_to(ROOT))
    print('集計完了。lec04_results.zipをダウンロードしてください。')

def main():
    p=argparse.ArgumentParser();p.add_argument('step',choices=['generate','label-basic','label-my','grade','report']);p.add_argument('--model');a=p.parse_args()
    if a.step=='generate':
        cases=judge.read_jsonl(MY)
        if any(c.get('answer') for c in cases): raise SystemExit('既存回答があります。生成済み回答を再生成しません')
        judge.main(['--generate','--cases',str(MY)])
    elif a.step.startswith('label-'): label(a.step.split('-')[1])
    elif a.step=='grade': grade(a.model)
    else: report()
if __name__=='__main__': main()
