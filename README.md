# AIE2026 演習・宿題リポジトリ

AIエンジニアリング実践講座（AIE2026）の演習と宿題で使うリポジトリです。
講座を通して、**AIエンジニアリングの学習を支援するエージェント**を少しずつ育てていきます。

## 想定する環境

演習は **ブラウザだけで** 進められるように作っています。自分の PC への導入は不要です。

| 使うもの | 用途 | 注意 |
|---|---|---|
| GitHub の **個人** アカウント | このリポジトリを fork し、作業ブランチと PR で提出する | 会社や学校が管理するアカウントでは Codespaces・Copilot が制限されることがあります |
| GitHub Codespaces | 第1・3・5回などの開発環境。`.devcontainer/` の設定で Python 3.12・uv・Node.js が入ったコンテナが自動で用意されます | 個人アカウントの無料枠は月 120 コア時間（2 コアで約 60 時間）。**使い終わったら停止**してください |

| GitHub Copilot（Free でよい） | コードの補完とチャット。第5回の発展課題では MCP クライアントとしても使います | Free は補完・チャットの回数に月の上限があります |
| OpenAI API | LLM の呼び出し。OpenAI Platform で API キーを発行し、Codespaces secret `OPENAI_API_KEY` で渡します | ChatGPT の契約と API の利用料・上限は別です |

| Google Colab（T4 GPU、無料枠） | 第2回の LoRA 学習だけに使います | GPU の利用時間に上限があります。終わったらランタイムを削除してください |

自分の PC で動かす場合は、Python 3.12 と [uv](https://docs.astral.sh/uv/) を入れて `uv sync --frozen` を実行し、環境変数 `OPENAI_API_KEY` を設定してください。

## はじめに（第1回）

1. このリポジトリを自分のアカウントに **fork** する
2. [OpenAI Platform](https://platform.openai.com/api-keys) で API キーを作る（ChatGPT の契約とは別に API の利用設定・支払いが必要です）
3. GitHub の **Settings → Codespaces → Secrets** に `OPENAI_API_KEY` を登録し、使う repository に自分の fork を選ぶ
4. 自分の fork で **Code → Codespaces → Create codespace on main**
5. ターミナルで動作確認

```bash
uv run pytest -q
uv run python -m app.ask "LoRAとは何ですか？"
```

詳しい手順は [lectures/01/problem.md](lectures/01/problem.md) を見てください。

## 第5回：講義資料を検索する

演習・宿題の手順は [lectures/05/problem.md](lectures/05/problem.md)、結果の記入先は [lectures/05/answer.md](lectures/05/answer.md) です。

第1〜3回の本講義214ページを埋め込んだ検索DB `data/rag_data/index.sqlite3` を同梱しています。`GEMINI_API_KEY` を設定し、リポジトリ直下で依存関係をそろえたら、検索や回答を試せます。検索時の質問の埋め込みと回答生成にはAPIを使います。

```bash
uv sync --frozen
uv run python -m app.retrieval "LoRA QLoRA 違い"
uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"
uv run python -m app.agent --graph --trace "LoRAとQLoRAの違いは？"
```

教材本文や埋め込み設定を変更した場合は、実験用のDBを作ります。`AIE_RAG_DB` を設定したターミナルでは、作成と検索の両方がそのパスを使います。

```bash
export AIE_RAG_DB="$PWD/.cache/rag/custom.sqlite3"
uv run python -m scripts.build_rag_index
```

同じ実験用DBを再作成する場合は、作成コマンドに `--rebuild` を付けます。同梱DBに戻すときは `unset AIE_RAG_DB` を実行します。Treeモード（`--tree`）と全文投入（`--full-context`）には検索DBは不要です。

## 構成

```
.devcontainer/   Codespaces の環境定義（Python 3.12、uv、Node.js。起動時に uv sync --frozen）
.github/workflows/test.yml  PR ごとにテストを実行（fork では Actions タブで有効化が必要）
app/
  config.py      モデル名とAPIキーの読み込み
  ask.py         第1回：LLMに質問する
  tools.py       第3回：エージェントのツール（用語集の検索など）
  agent.py       第3回：Pydantic AI の学習支援エージェント（第5回：講義資料の検索を使う）
  judge.py       第4回：評価セットを LLM に採点させ、人のラベルとの一致率を出す
  retrieval.py   第5回：講義資料の検索・Tree探索・Graph探索・全文投入
  mcp_server.py  第6回：用語集を公開する MCP サーバー
  mcp_agent.py   第6回：MCP サーバーのツールを使うエージェント（MCP クライアント）
  mcp_servers.json 第6回：使う MCP サーバーの設定（mcpServers 形式）
data/
  glossary.json  講座の用語集
  lectures/      各回の要点
  eval/          第4回：評価セット（lec04_cases.jsonl）と採点の基準（rubric.md）
  rag_data/      第5回：講義資料本文（lectures.json）、目次（tree.json）、ページ・用語の関係（graph.json）、検索DB（index.sqlite3）
tools/
  annotate.py    第4回：評価セットにラベルを付ける画面（Streamlit。uv run --with で一時的に足して動かす）
.streamlit/      Streamlit の設定（Codespaces のポート転送で開けるようにする）
lectures/NN/
  problem.md     その回の演習と宿題
  answer.md      あなたが記入して提出するファイル
notebooks/       第2回：Google Colab で動かす LoRA のノートブック（lora_format_tuning.ipynb）
scripts/
  build_rag_index.py 第5回：教材を埋め込み、検索DBを作成する
  make_sft_dataset.py 第2回：学習データの準備
tests/           テスト（APIキー不要）
pyproject.toml / uv.lock  依存パッケージとその固定版
```

## 提出のしかた

1. 回ごとに作業ブランチを作る（例：`git switch -c lec01`）
2. 演習・宿題を行い、`lectures/NN/answer.md` に記入する
3. push して、**自分の fork の中で** 作業ブランチ → `main` の PR を作る

宿題は「基礎・実装・発展」の3レベルがあり、どれか1つに取り組めば完了です。

## 前提と制約
- **依存パッケージの版は固定**しています（`uv.lock`。Python 3.12、pydantic-ai-slim 2.57.0、openai 3.35.1）。講座の期間中は上げません。`uv sync --frozen` でそのまま入れてください。
- **既定のモデルは `gpt-4o-mini`** です。環境変数 `AIE_MODEL` で切り替えられます（下の「モデルの切り替え」）。利用できるモデルは OpenAI API のアカウント設定を確認してください
- **API の利用料とレート制限**は ChatGPT の契約とは別に OpenAI Platform 側で管理されます。エージェント（第3回以降）は 1 つの質問で LLM を複数回呼ぶため、利用状況と上限に注意してください
- **API キーは環境変数 `OPENAI_API_KEY` だけ**で渡します。コード・コミット・チャットに貼らないでください。漏れたら OpenAI Platform で削除して作り直します
- Codespaces からインターネットへは出られますが、外から Codespaces の中へは接続できません（ポート転送は既定で非公開）。第5回の MCP サーバーは Codespaces の中で動かします

- テスト（`uv run pytest -q`）は API キーなしで動きます（LLM を呼ばない TestModel を使用）

## 守ってほしいこと

- **APIキーをコードやコミットに書かない。** Codespaces secret で渡します
- **使い終わったら Codespaces を停止する。** 無料枠を使い切ると起動できなくなります
- AIツール（Copilot など）は使ってかまいません。提案されたコードは、読んで理解してから採用してください

## モデルの切り替え

既定モデルは `gpt-4o-mini` です。環境変数 `AIE_MODEL` で切り替えられます。

```bash
AIE_MODEL=gpt-4o uv run python -m app.ask "LoRAとは何ですか？"
```

利用可能なモデル・料金・レート制限は [OpenAI API のドキュメント](https://platform.openai.com/docs) で確認してください。
