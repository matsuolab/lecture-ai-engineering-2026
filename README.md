# AIE2026 演習・宿題リポジトリ

AIエンジニアリング実践講座（AIE2026）の演習と宿題で使うリポジトリです。
講座を通して、**AIエンジニアリングの学習を支援するエージェント**を少しずつ育てていきます。

## 想定する環境

演習は **ブラウザだけで** 進められるように作っています。自分の PC への導入は不要です。

| 使うもの | 用途 | 注意 |
|---|---|---|
| GitHub の **個人** アカウント | このリポジトリを fork し、作業ブランチと PR で提出する | 会社や学校が管理するアカウントでは Codespaces・Copilot が制限されることがあります |
| GitHub Codespaces | 第1・3・5回などの開発環境。`.devcontainer/` の設定で Python 3.12・uv・Node.js が入ったコンテナが自動で用意されます | 個人アカウントの無料枠は月 120 コア時間（2 コアで約 60 時間）。**使い終わったら停止**してください |
| GitHub Copilot（Free でよい） | コードの補完とチャット。第6回の発展課題では MCP クライアントとしても使います | Free は補完・チャットの回数に月の上限があります |
| Gemini API（Google AI Studio の無料枠） | LLM の呼び出し。**個人**の Google アカウントでキーを発行し、Codespaces secret `GEMINI_API_KEY` で渡します | 無料枠には 1 分あたり・1 日あたりの上限があります（下の「前提と制約」） |
| Google Colab（T4 GPU、無料枠） | 第2回の LoRA 学習だけに使います | GPU の利用時間に上限があります。終わったらランタイムを削除してください |

自分の PC で動かす場合は、Python 3.12 と [uv](https://docs.astral.sh/uv/) を入れて `uv sync --frozen` を実行し、環境変数 `GEMINI_API_KEY` を設定してください。

## はじめに（第1回）

1. このリポジトリを自分のアカウントに **fork** する
2. [Google AI Studio](https://aistudio.google.com/apikey) で Gemini API キーを作る
3. GitHub の **Settings → Codespaces → Secrets** に `GEMINI_API_KEY` を登録し、使う repository に自分の fork を選ぶ
4. 自分の fork で **Code → Codespaces → Create codespace on main**
5. ターミナルで動作確認

```bash
uv run pytest -q
uv run python -m app.ask "LoRAとは何ですか？"
```

詳しい手順は [lectures/01/problem.md](lectures/01/problem.md) を見てください。

## Day1: LLM質問・評価・モデル選定

### 目的と主要機能

Gemini APIを使う最小の質問アプリを題材に、会話履歴、実行計測、評価証拠に基づくモデル候補選定を試します。

- `app.ask` は従来の単発質問に加え、会話履歴付きの対話と、複数の質問・モデルを指定回数実行する比較モードを提供します。
- モデルは `AIE_MODEL` で変更でき、`--temperature` で生成temperatureを指定できます。
- 応答時間、トークン数、成功・失敗、エラー種別を `learning_log/ask_metrics.csv` に追記します。
- 比較時だけ、比較に必要な質問文と回答を `learning_log/ask_comparisons.csv` に保存します。ログディレクトリはGit管理対象外です。
- `app.model_selection` は設定可能なAcceptance CriteriaとJSONの評価証拠から、Hard Gate、統計、Markdownレポートを作ります。未知情報の品質は自動キーワード採点せず、ケースごとの人手レビュー結果を使います。

### 講義指定課題と独自追加機能

**講義指定課題**は、同一質問の反復・モデル切り替え（基礎）、会話履歴の実装（実装）、時間・トークン計測と複数モデル／質問の比較（発展）です。実装状態と実測結果は[Day1解答](lectures/01/answer.md)に記載しています。

**独自追加機能**は、Acceptance Criteria設定、最低試行数を踏まえた必須要求のHard Gate、EvidenceからのMarkdownレポート生成、Pass／Fail／Inconclusive／Not Evaluatedの分離、API実行成功率と回答品質の分離、人手レビュー根拠の記録です。Q2各試行の暫定照合と人手確認欄は[Q2レビュー表](lectures/01/q2_review.md)を参照してください。判定は人手の最終評価ではありません。

公開可能な実API Evidenceは [evidence/day1_gemini_experiments.json](evidence/day1_gemini_experiments.json) です。旧・新実験の全36試行について、実験ID、モデル、質問ID、試行番号、日時、temperature、応答時間、トークン数、実行状態、HTTPステータス、質問文と回答を許可リスト方式で収録します。APIキー・認証情報・個人情報・未加工の例外本文は出力対象にしていません。元の生Evidenceと個人ログは `.gitignore` 対象の `learning_log/` に変更せず保持します。公開Evidenceから集計を再計算し、生Evidenceとの実験ID・測定値一致をテストします。

### システム構成

| ファイル | 役割 |
|---|---|
| `app/config.py` | Geminiモデル名とAPIキーの設定 |
| `app/ask.py` | Gemini API呼び出し、会話、比較、CSV計測 |
| `app/model_selection.py` | JSON証拠の集計、Hard Gate判定、Markdownレポート |
| `app/public_evidence.py`, `scripts/export_public_evidence.py` | 保存済みEvidenceから許可項目だけを公開JSONに変換し、集計を再計算 |
| `data/model_evaluation_criteria.json` | 評価閾値と必須要件 |
| `data/model_evaluation_cases.json` | 未知情報・APIエラー・既知回答の評価ケース |
| `data/model_evaluation_sample.json` | 出力確認用の合成モック証拠 |
| `tests/test_ask.py`, `tests/test_model_selection.py`, `tests/test_public_evidence.py` | APIキー不要のテスト。ローカルに生Evidenceがあれば公開版との照合も行う |

### 実行方法

```bash
# 従来の単発質問
uv run python -m app.ask "LoRAとは何ですか？"

# モデル切り替え。使用可能なモデル名は利用者側の環境で確認
AIE_MODEL=gemini-3.5-flash-lite uv run python -m app.ask "LoRAとは何ですか？"

# 会話。/reset で履歴初期化、/exit で終了
uv run python -m app.ask --chat

# 3質問 × 2モデル × 各3回（合計18回のAPI呼び出し）
# 実APIを呼び出す。実行前にFree Tier・課金状態・利用可能枠を確認し、
# 既存のEvidenceを上書きしない新しい出力パスを指定する。
uv run python -m app.ask --compare \
  --models gemini-3.5-flash-lite gemini-3.8-flash \
  --questions \
    "LoRAとは何ですか？" \
    "AIE2026の宿題の3レベルとは何ですか？" \
    "E2E自動運転システムの検証方法を説明してください。" \
  --runs 3 --temperature 0.2 \
  --evidence-output learning_log/ask_evidence_reproduction.json

# 生成した実験Evidenceを評価（追加のGemini API呼び出しなし）
uv run python -m app.model_selection \
  --input learning_log/ask_evidence_reproduction.json \
  --criteria data/model_evaluation_criteria.json \
  --cases data/model_evaluation_cases.json \
  --output learning_log/model_selection_report_reproduction.md

# 合成モック証拠のレポート確認（Gemini API呼び出しなし）
uv run python -m app.model_selection \
  --input data/model_evaluation_sample.json \
  --output /tmp/model_selection_sample_report.md

# 全テスト（Gemini APIキー不要）
uv run pytest -q
```

保存済みの生Evidenceから公開用ファイルを再生成する場合（生成API呼び出しなし）：

```bash
uv run python -m scripts.export_public_evidence
```

既定の出力先は `evidence/day1_gemini_experiments.json` です。変換器は許可リスト方式で項目を選び、認識可能な秘密情報やメールアドレスを検出した場合は出力を拒否します。公開前にもEvidence本文を確認してください。

3質問を2モデルで各3回実行する場合は、生成API呼び出しが最大18回です。比較実行は各試行ラウンドでモデル順を交互にし、リトライしません。429を検出した時点で残りを送らず、未実行試行としてEvidenceに残します。比較CSVからEvidence JSONは自動生成されます。実験時のキー利用可否だけでは無料枠残量・課金状態は判定できないため、API利用前にGoogle AI Studio側で利用枠と課金設定を確認してください。

`5秒以内` は実験用の仮閾値で、講義指定や本番SLOではありません。必須ゲートは個別にPass/Fail/Not Evaluated/Inconclusiveを表示し、Failがあれば不適合、未評価・判定不能は合格扱いにしません。応答時間中央値が優れたモデルを選ぶ場合も、全ゲートのPassと同一条件の証拠が必要です。

### 出力例（合成モックデータ）

サンプル評価器は、形式確認用の架空証拠に対して以下のような判定を出します。これはGeminiの測定値でも、実際のモデル優劣でもありません。

```text
mock-model-alpha: 応答時間 Inconclusive / APIエラー Inconclusive / 未知情報 Inconclusive
mock-model-beta:  応答時間 Fail（超過観測あり） / APIエラー Inconclusive / 未知情報 Fail
選定候補: なし（モックサンプルは最低3試行に不足）
```

### 実測結果と失敗分析（2026-10-25）

以下の測定値は実API結果です。回答本文を含む全36試行の公開Evidenceは [evidence/day1_gemini_experiments.json](evidence/day1_gemini_experiments.json) から確認できます。元の生Evidenceは `learning_log/` に保持し、公開ファイル生成時も変更していません。

- ローカル詳細分析：`learning_log/experiment_analysis_20261025.md`（質問別成功・失敗時間、出力tokenとの関係、Q2照合）
- ローカル新実験Evidence：`learning_log/ask_evidence_20261025_gemini38.json`、実験ID `ef65d5d3-a3ed-4215-8831-18a0e43dbd06`
- ローカル新実験レポート：`learning_log/model_selection_report_20261025_gemini38.md`
- ローカル旧実験Evidence：`learning_log/ask_evidence.json`（新実験で上書きせず保持）
- Q2公開レビュー表：[一般定義とDay1具体課題を分けた試行別照合](lectures/01/q2_review.md)

新実験（temperature 0.2、各モデル9回）では、`gemini-3.5-flash-lite` が9/9成功、応答時間平均／中央値／最大は3.365／2.850／5.087秒。`gemini-3.8-flash` は4/9成功、5/9がHTTP 503で、成功応答は199.549／210.360／227.484秒でした。3.8 Flashの95.230秒スモークテストは別測定のため、この統計には含めていません。5秒は実験用の仮閾値であり、両モデルとも応答時間Hard GateはFail、未知情報とエラー処理の品質ゲートはNot Evaluatedです。Q2の回答には講義用語集と異なる一般論があり、品質の最終判定は人手レビュー待ちです。詳細な404/503の失敗分析と評価限界は上記分析資料を参照してください。少数ケースの実測は実運用上の品質保証ではありません。

### Day1課題との対応

| 課題 | 対応 |
|---|---|
| 基礎 | `AIE_MODEL` とtemperatureを変更可能。比較モードで同一質問をモデルごとに3回実行し回答を保存。実API比較結果と考察は上記実験分析に記録 |
| 実装 | `--chat` で会話履歴を引き継ぎ、`/reset` で初期化。既存の単発CLIを維持 |
| 発展 | `time.perf_counter()`、トークン数、エラー種別を記録し、複数モデル・質問を比較。実測した応答時間・503・トークン数・Hard Gateの考察を実験分析に記録 |

### 独自に追加した工夫

- 性能値と人手レビューをEvidence JSONとして追跡し、評価条件・判定根拠もレポートに残す。
- Acceptance Criteriaを設定ファイルに分離し、閾値をコード変更なしで調整可能にする。
- 5秒境界、トークン欠損、APIエラー、曖昧なレビューを明示してテストする。
- 自動品質スコアやLLM-as-a-Judgeは設けず、未知情報の回答は人手評価の状態と根拠を記録する。
- 未知情報ケースの人手レビューでは回答の引用と判断理由を残し、Pass／Fail／Inconclusiveを区別する。比較実行だけでは未知情報・APIエラー処理の品質を自動Passにしない。

未知情報ケースのレビュー基準は、[data/model_evaluation_cases.json](data/model_evaluation_cases.json) に記載しています。Passは「情報がないと伝え、具体的な内容を捏造しない」、Failは「未確認の内容を事実として断定する」、Inconclusiveは「判断が分かれる曖昧な回答」です。判断根拠には回答からの短い引用と基準との対応を記録します。評価フィールドが空の場合は自動Passになりません。

## 第5回：講義資料を検索する

演習手順と記録先は[lectures/05/problem.md](lectures/05/problem.md)、[lectures/05/answer.md](lectures/05/answer.md)です。基本RAG・Tree・Graph・Adaptive Graphは第1〜3回の本講義資料214ページを使い、Full Contextは教材JSON全体を渡します。検索時のquery embeddingと回答生成にはGemini APIを使用します。

```bash
# 基本RAG（search_materials tool）
uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"

# Graph方式の比較
uv run python -m app.agent --graph --trace "LoRAとQLoRAの違いは？"
uv run python -m app.agent --adaptive-graph --trace "LoRAとQLoRAの違いは？"
uv run python -m app.agent --tree --trace "LoRAとQLoRAの違いは？"
uv run python -m app.agent --full-context --trace "LoRAとQLoRAの違いは？"

# 検索結果だけを確認（回答生成なし。ただしquery embeddingにはAPIを使用）
uv run python -m app.retrieval "LoRA QLoRA 違い"
```

Adaptive GraphはLLMが作る短いqueryをベクトル検索に使い、充足性判定には元の質問を渡します。`--trace`では取得ページ、論点別の判定、Graphの探索経路、時間・トークン・推定費用を確認できます。充足判定はルールベースの参考値で、意味的な根拠充足を保証しません。

同梱の `data/rag_data/index.sqlite3` を検索DBとして使います。教材本文や埋め込み設定を変える場合は、同梱DBを変更せず、実験用DBを指定します。

```bash
export AIE_RAG_DB="$PWD/.cache/rag/custom.sqlite3"
uv run python -m scripts.build_rag_index
```

再作成時はbuildコマンドに `--rebuild` を付けます。同梱DBへ戻す場合は `unset AIE_RAG_DB` を実行してください。`uv sync --frozen` で固定依存をインストールします。比較する質問・モデル・対象資料は各方式でそろえ、API利用枠を確認してから実行してください。

## 構成

```
.devcontainer/   Codespaces の環境定義（Python 3.12、uv、Node.js。起動時に uv sync --frozen）
.github/workflows/test.yml  PR ごとにテストを実行（fork では Actions タブで有効化が必要）
app/
  config.py      モデル名とAPIキーの読み込み
  ask.py         第1回：LLMに質問する
  tools.py       第3回：エージェントのツール（用語集の検索など）
  agent.py       第3回：Pydantic AI の学習支援エージェント（第6回：--mcp で MCP 経由）
  judge.py       第4回：評価セットを LLM に採点させ、人のラベルとの一致率を出す
  mcp_server.py  第6回：用語集を公開する MCP サーバー
  mcp_servers.json 第6回：使う MCP サーバーの設定（mcpServers 形式）
data/
  glossary.json  講座の用語集
  lectures/      各回の要点
  eval/          第4回：評価セット（lec04_cases.jsonl）と採点の基準（rubric.md）
tools/
  annotate.py    第4回：評価セットにラベルを付ける画面（Streamlit。uv run --with で一時的に足して動かす）
.streamlit/      Streamlit の設定（Codespaces のポート転送で開けるようにする）
lectures/NN/
  problem.md     その回の演習と宿題
  answer.md      あなたが記入して提出するファイル
notebooks/       第2回：Google Colab で動かす LoRA のノートブック（lora_format_tuning.ipynb）
scripts/         補助スクリプト
tests/           テスト（APIキー不要）
pyproject.toml / uv.lock  依存パッケージとその固定版
```

## 提出のしかた

1. 回ごとに作業ブランチを作る（例：`git switch -c lec01`）
2. 演習・宿題を行い、`lectures/NN/answer.md` に記入する
3. push して、**自分の fork の中で** 作業ブランチ → `main` の PR を作る

宿題は「基礎・実装・発展」の3レベルがあり、どれか1つに取り組めば完了です。

## 前提と制約

- **依存パッケージの版は固定**しています（`uv.lock`。Python 3.12、pydantic-ai-slim 2.57.0、google-genai 2.31.0）。講座の期間中は上げません。`uv sync --frozen` でそのまま入れてください。
- **既定のモデルは `gemini-3.5-flash-lite`** です。環境変数 `AIE_MODEL` で切り替えられます（下の「モデルの切り替え」）。ほかのモデルや自前契約の API を使ってもかまいません
- **Gemini API の無料枠にはレート制限**があります。エージェント（第3回以降）は 1 つの質問で LLM を複数回呼ぶので、第1回より早く上限に達します。`レート制限に達しました` と出たら 1 分ほど待ってください。`モデルが混み合っています（503）` が続くときは `AIE_MODEL=gemini-3.1-flash-lite` を試してください
- **API キーは環境変数 `GEMINI_API_KEY` だけ**で渡します。コード・コミット・チャットに貼らないでください。漏れたら AI Studio で削除して作り直します
- Codespaces からインターネットへは出られますが、外から Codespaces の中へは接続できません（ポート転送は既定で非公開）。第6回の MCP サーバーは Codespaces の中で動かします
- テスト（`uv run pytest -q`）は API キーなしで動きます（LLM を呼ばない TestModel を使用）

## 守ってほしいこと

- **APIキーをコードやコミットに書かない。** Codespaces secret で渡します
- **使い終わったら Codespaces を停止する。** 無料枠を使い切ると起動できなくなります
- AIツール（Copilot など）は使ってかまいません。提案されたコードは、読んで理解してから採用してください

## モデルの切り替え

既定モデルは `gemini-3.5-flash-lite` です。環境変数 `AIE_MODEL` で切り替えられます。

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "LoRAとは何ですか？"
```

無料枠には1分あたり・1日あたりのリクエスト上限があります。上限は [Gemini API のレート制限のページ](https://ai.google.dev/gemini-api/docs/rate-limits) で確認してください。
