# AIE2026 第1回 — 発展＋Plus α：LLMの「速さ × コスト × 信頼性」評価

## 研究上の狙い

第1回「実装」の `--chat` と演習のトークン数表示も併せて実装済み。

単純なレイテンシ比較を拡張し、講座固有の事実を質問した際、参照できる資料の有無で「回答の正しさ」と「リソース使用」がどう変化するかを検証する。

- **評価軸1（発展）**：モデル別の壁時計レイテンシ、入力・出力・思考・総トークン、失敗率。
- **評価軸2（Plus α）**：正答定義を付与した場合の正確性、誤った断定の頻度、トークン効率。
- **陰性対照**：関係のない資料を渡す条件を加え、「資料を付与する操作」と「正しい知識を与えること」を分けて考える（長さの完全一致はしない）。

## 実験要因と回数

| 変数 | 条件 |
|---|---|
| モデル | `gemini-3.5-flash-lite`、`gemini-3.6-flash` |
| 質問 | 宿題の3レベル、`lecNN-start`タグ、講座の既定モデルと採用理由 |
| 参照資料 | なし、無関係なLoRA定義、関連する正解定義 |
| 反復 | 各条件3回、seed固定のシャッフル |
| 生成設定 | max_output_tokens=1024、それ以外はSDK既定値 |
| 計画リクエスト | 2 × 3 × 3 × 3 = **54回** |

使用される正解は既存の `data/glossary.json`。回答はインターネットから収集した任意の「正解」ではなく、コースの一次資料を基準にする。モデルには検索ツールを使わせない。モデルの内部思考設定は必ずしも同一ではないため、速度差をモデルアーキテクチャの差だと断定しない。

## Codespacesでの実行手順

作業ブランチ上で本パッケージの変更ファイルをリポジトリの同じ相対パスへコピーする。**元の `data/glossary.json` や `app/config.py` は変更しない**。

### 1. Python環境とテスト

```bash
uv sync --frozen
uv run pytest -q
uv run python -m scripts.lec01_advanced plan
```

### 2. 安全なスモークテスト（APIを3回呼ぶ）

あらかじめGitHub Codespaces secret `GEMINI_API_KEY` を設定しておく。**APIキーはターミナル・チャット・ソースへ直接貼り付けない**。

```bash
uv run python -m scripts.lec01_advanced run \
  --models gemini-3.5-flash-lite \
  --questions homework-levels --repeats 1 --pause 5 \
  --output-dir outputs/lec01_smoke
```

### 3. 本実験（初回54リクエスト）

```bash
uv run python -m scripts.lec01_advanced run --pause 5
```

無料枠や契約状況によっては54回すべてを実行できない場合がある。429や503を含む失敗も記録するので、実行不能だったリクエストは無理に成功扱いしない。実行中断後、**同じコマンド**で再開できる（成功分をスキップ）。**モデルや質問・反復回数を変える場合は別の出力ディレクトリを使う**。

*注*: `run` は実行済み結果を `answer.md` 内の専用マーカー範囲に転記する。スモークテストでも一時的にこの欄が更新されるため、**本実験後に再度 `run` を実行して上書きすること**。

### 4. 正確性・ハルシネーションを手動評価

`outputs/lec01_advanced/review.csv` を表計算ソフトなどで開き、各回答について `accuracy_score` と `hallucination` を記入する。

- `accuracy_score=2`：質問の重要事実がすべて正確で、明確な矛盾がない
- `accuracy_score=1`：一部は合っているが、不十分・曖昧
- `accuracy_score=0`：誤りがある、具体的な内容がない、あるいは不明と回答した
- `hallucination=yes`：事実と違うことを断定した
- `hallucination=no`：誤った事実の断定はない（「不明」も含む）
- `hallucination=unclear`：資料だけでは確定できない

ルールを先に決めてから採点し、正確性とハルシネーションを混同しない。回答の採点はモデルに依頼せず、出典を確認して人手で行う。可能なら回答の条件名を隠した別の評価者にも採点してもらい、一致度を確認すると研究としての説得力が上がる。

```bash
uv run python -m scripts.lec01_advanced analyze
```

`summary.md`、`comparison.svg` が更新され、`lectures/01/answer.md` の実測欄へ結果が転記される。

## 出力ファイル

| ファイル | 用途 |
|---|---|
| `measurements.csv` | 呼び出しごとの所要時間、トークン数、成否（APIキーは含めない） |
| `responses.jsonl` | 再現・事後分析用の応答本文 |
| `manifest.json` | 実行条件、seed、用語集SHA-256 |
| `review.csv` | 監査可能な人手採点表 |
| `summary.md` | 条件別記述統計とペア差、考察上の制限 |
| `comparison.svg` | レイテンシと総トークン数の比較図 |

本実験の生データは `/outputs/lec01_advanced/` に保存される。**プライバシー・APIキー・不要なファイル混入を防ぐため、ルート `.gitignore` に `/outputs/lec01_advanced/` を追記すること**（既存の `.gitignore` は上書きしない）。スモークの出力にも同様に `/outputs/lec01_smoke/` を追記すること。

## 解釈と制約

- 「grounded」が良い場合でも、**正答を直接渡している**ので自動的な情報検索の成功ではない。比較対象は外部知識を与えた場合の生成品質。
- 陰性対照の用語集定義は対象質問と同じトークン長に揃えていない。入力の長さ自体による影響が残る。
- n=3/質問の短期計測は安定した推論性能の証明にならない。日時・繰返し条件を増やした追試が必要。
- `response.usage_metadata` が欠損した場合は不明として扱い、ゼロ埋め・想像値の補完はしない。
- SDKは一時的なエラーを自動再試行する可能性があるため、レイテンシは**純粋なモデル推論時間**ではない。
- 料金を求める場合、モデル・課金プラン・思考トークン・出入力単価が必要。現時点では価格の確定値を作らない。

### 公式の参考資料

- 講座の課題文：`lectures/01/problem.md` と `data/glossary.json`
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/api-errors
- https://ai.google.dev/gemini-api/docs/models
- https://googleapis.github.io/python-genai/
