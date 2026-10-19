"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --benchmark  # JSONから一括計測・回答欄更新
    uv run python -m app.ask --report-only  # 保存済み結果から回答欄のみ更新
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from statistics import median
from time import perf_counter, sleep

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    from google import genai

    client = genai.Client(api_key=get_api_key())
    started = perf_counter()
    response = client.models.generate_content(model=MODEL, contents=question)
    elapsed = perf_counter() - started

    print(f"[応答時間] {elapsed:.3f} 秒")
    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")

    return response.text


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lectures/01/benchmark_3_8.json'
ANSWER = ROOT / 'lectures/01/answer.md'


def load_data():
    data = json.loads(DATA.read_text())
    if not isinstance(data, dict):
        raise SystemExit('JSONはmodels・questions・resultsを持つオブジェクトにしてください。')
    models = data['models']
    questions = data['questions']
    if not models or len(models) != len(set(models)):
        raise SystemExit('modelsは重複のないモデル名のリストにしてください。')
    ids = [q['id'] for q in questions]
    if not ids or len(ids) != len(set(ids)) or any(not q['text'].strip() for q in questions):
        raise SystemExit('質問のidは重複不可、textは空欄不可です。')
    if data.get('interval_seconds', 60) < 0:
        raise SystemExit('interval_secondsは0以上にしてください。')
    return data


def matches(record, model, question):
    return (record['model'] == model and record['question_id'] == question['id']
            and record['question'] == question['text'])


def write_report(data):
    original = ANSWER.read_text()
    prefix = original.split('## 宿題', 1)[0]
    lines = ['## 宿題', '', '- 取り組んだレベル：発展', '', '- やったこと：', '',
             '  `benchmark_3_8.json`に全モデル・質問・測定結果をまとめ、`app/ask.py`で未計測の組合せを計測し、この宿題欄を自動生成した。',
             '  応答時間はAPI呼び出し直前から回答全体の受信まで。通信・待機・生成時間を含み、クライアント作成時間は含まない。入力はprompt_token_count、出力はcandidates_token_countである。', '',
             '  登録モデル：' + '、'.join(data['models']), '']
    for q in data['questions']:
        lines.append(f"  - {q['id']}：{q['text']}")
    lines += ['', '- 結果：', '',
              '  計測済みの成功値を集計した。複数回ある条件は中央値を表示する。「未計測」はAPIの成功結果がない条件。質問本文を変更すると別条件として扱う。', '',
              '  | モデル | 質問 | 成功回数 | 応答時間（秒） | 入力トークン | 出力トークン |',
              '  |---|---|---:|---:|---:|---:|']
    groups = {}
    for q in data['questions']:
        groups[q['id']] = []
        for model in data['models']:
            records = [r for r in data['results'] if matches(r, model, q) and 'error' not in r]
            if records:
                elapsed = median(r['seconds'] for r in records)
                counts = []
                for field in ('input_tokens', 'output_tokens'):
                    values = [r[field] for r in records if r.get(field) is not None]
                    counts.append(f'{median(values):g}' if values else '不明')
                lines.append(f"  | {model} | {q['id']} | {len(records)} | {elapsed:.3f} | {' | '.join(counts)} |")
                groups[q['id']].append((model, elapsed))
            else:
                lines.append(f"  | {model} | {q['id']} | 0 | 未計測 | — | — |")
    lines += ['', '- 気づき・疑問：', '']
    for qid, values in groups.items():
        if len(values) > 1:
            fastest = min(values, key=lambda x: x[1])
            slowest = max(values, key=lambda x: x[1])
            lines.append(f'  - {qid}：今回の観測で最短は{fastest[0]}（{fastest[1]:.3f}秒）、最長は{slowest[0]}（{slowest[1]:.3f}秒）。差は{slowest[1] - fastest[1]:.3f}秒だった。')
    lines += ['  - 各条件の測定回数が少なく、実行時刻も異なる。観測値から恒常的な速度差や回答品質の優劣は断定できない。質問内容と指定文字数を同時に変えているため、それぞれの影響も切り分けられない。',
              '  - 応答時間には通信・サーバー待機・モデル内部の処理も含まれる。出力トークン数だけで所要時間を説明できず、文字数とトークン数も一致しない。',
              '  - 無料枠の主な制限はRPM（毎分リクエスト数）、入力TPM（毎分入力トークン数）、RPD（毎日リクエスト数）。いずれかを超えると制限される。具体的な上限と無料枠の対象モデルはAI Studioで確認する必要がある。今回の成功記録だけでは無料枠で実行したかは判定できない。',
              '  - 短い質問の連続実行ではRPM、長い入力では入力TPMに注意する。出力トークンは入力TPMと区別する。質問とモデルを増やすほどAPI呼び出し回数も増える。既定の60秒間隔は上限内での実行を保証せず、同じプロジェクトの他の利用も考慮する必要がある。',
              '  - 制限はプロジェクト単位。429の原因が分単位の枠なら待機で回復し得るが、RPD枯渇なら1分待つだけでは回復しない。RPDは太平洋時間の午前0時にリセットされる。エラーは成功値に混ぜず記録する。',
              '  - 参考：[Google公式のレート制限](https://ai.google.dev/gemini-api/docs/rate-limits)（2026年10月19日確認）', '',
              '### 各回の測定記録', '']
    for r in data['results']:
        lines += [f"#### {r['model']} / {r['question_id']}（{r.get('measured_at') or '日時未記録'}）", '', r['question'], '']
        if 'error' in r:
            lines += [f"APIエラー：HTTP {r.get('status', '不明')}（詳細はJSONを参照）", '']
        else:
            lines += [f"応答時間：{r['seconds']:.3f}秒、入力：{r.get('input_tokens')}、出力：{r.get('output_tokens')}", '']
            lines += [('> ' + line).rstrip() for line in (r.get('answer') or '回答本文未保存').splitlines()]
            lines.append('')
    ANSWER.write_text(prefix + '\n'.join(lines).rstrip() + '\n')
    print(f'更新しました: {ANSWER}', flush=True)



def benchmark(report_only=False):
    print("ベンチマークを開始します。JSONを読み込み中…", flush=True)
    data = load_data()
    write_report(data)
    if report_only:
        return
    pending = [(m, q) for q in data['questions'] for m in data['models']
               if not any(matches(r, m, q) and 'error' not in r for r in data['results'])]
    if not pending:
        print('全組合せが計測済みです。APIは呼び出しません。')
        return
    print(f'未計測は{len(pending)}件です。', flush=True)
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        raise SystemExit('レポートは更新済み。追加計測にはAPIキー設定済みのターミナルで実行してください。')
    print('Geminiライブラリを読み込み中…（この段階ではAPIは呼び出していません）', flush=True)
    from google import genai
    from google.genai import errors
    print('ライブラリの読み込み完了。APIクライアントを準備します。', flush=True)
    with genai.Client(api_key=key, http_options={"timeout": 90000}) as client:
        for index, (model, q) in enumerate(pending):
            if index:
                interval = data.get('interval_seconds', 60)
                print(f'次の計測まで{interval}秒待機します。', flush=True)
                sleep(interval)
            print(f"計測中: {model} / {q['id']}", flush=True)
            record = dict(model=model, question_id=q['id'], question=q['text'],
                          measured_at=datetime.now().astimezone().isoformat())
            started = perf_counter()
            try:
                response = client.models.generate_content(model=model, contents=q['text'])
                elapsed = perf_counter() - started
                usage = response.usage_metadata
                record.update(seconds=elapsed, input_tokens=usage.prompt_token_count if usage else None,
                              output_tokens=usage.candidates_token_count if usage else None, answer=response.text)
            except errors.APIError as exc:
                record.update(status=exc.code, error=exc.message)
                print(f'HTTP {exc.code}: 失敗として記録します。', flush=True)
            data['results'].append(record)
            DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            write_report(data)



def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--benchmark", action="store_true", help="JSONの未計測モデル・質問を実行してanswer.mdを更新")
    mode.add_argument("--report-only", action="store_true", help="APIを呼ばずにJSONからanswer.mdを更新")
    args = parser.parse_args()
    if args.benchmark or args.report_only:
        benchmark(report_only=args.report_only)
        return

    from google.genai import errors

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
