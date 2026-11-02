# 第3回 演習・宿題：学習支援エージェントを作る

## この回のゴール

- エージェントが「モデル＋ループ＋ツール」でできていることを、自分のコードで確かめる
- どのツールが、どの引数で呼ばれたかを読める
- ツールを1つ追加できる

## 演習（30分）

最初の約5分で第2回の宿題を解説します。その間に、手順1の Sync fork を押し、Codespaces を起動しておきましょう（起動に数分かかります）。

### 1. 講座 repo の更新を取り込み、lec03 ブランチを作る

講座 repo の修正を自分の fork に取り込んでから、作業ブランチを作ります。

1. GitHub で自分の fork を開き、**Sync fork → Update branch** を押します（すでに最新なら Update branch は出ないので、何もしなくてかまいません）
2. Codespaces を起動し、ターミナルで次を実行します

```bash
git switch main
git pull --no-rebase
git switch -c lec03
```

- `git switch main` で止まる場合は、前の回のブランチに変更が残っています。前の回のブランチで commit してから、もう一度実行してください
- `a branch named 'lec03' already exists` と出た場合は、`lec03` はもう作ってあります。`git switch lec03` で切り替えてください
- `git pull --no-rebase` で `CONFLICT` と出た場合は、`git merge --abort` で元に戻してから、下の方法で始めてください（元に戻すので、自分の変更は消えません）

#### main が壊れた、または前の回までの作業が終わっていない場合

Sync fork で衝突の表示（Pull request の作成や「Discard commits」）が出た場合も、**押さずに**こちらで始めます。「Discard commits」を押すと、自分のコミットが消えます。

講座 repo の開始時点のコード（`lec03-start` タグ）からブランチを作ります。

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec03-start
git switch -c lec03 lec03-start
```

### 2. 第1回と同じ質問をエージェントに投げる

```bash
uv run python -m app.agent "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
```

第1回の `app.ask` の回答と比べてみましょう。エージェントは用語集を検索してから答えます。正しい内容は `data/glossary.json` の `homework-levels` にあります。

### 3. ツール呼び出しを読む

```bash
uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"
```

`[tool call]` の行で、モデルがどのツールをどんな引数で呼んだかを確認します。`[usage]` の `requests` は、1つの質問で LLM を何回呼んだかを表します。

なぜ答える前に検索するのか、なぜ用語を1つずつ検索するのかは、モデルへの指示に書いてあります。指示は2か所にあります。

- `app/agent.py` の `INSTRUCTIONS`（31行目付近）：エージェント全体への指示。「必ず search_glossary で用語集を確認する」「回答の最後に、関係する回（第N回）を示す」などが書いてあります
- `app/tools.py` の各ツールの docstring：ツールの説明文としてモデルに渡ります。`search_glossary` には「query には調べたい用語を1つだけ入れる」と書いてあります

宿題の基礎では、この2か所を書き換えて、ふるまいがどう変わるかを比べます。

### 4. make_quiz ツールを書いて登録する

「第2回の確認問題を出して」と頼まれたときに、エージェントが用語集から問題を作れるようにします。モデルが `make_quiz` を `lecture=2` で呼び、ツールが第2回の用語を1つ選んで問題と答えを返し、モデルがそれを使って出題します。

1. `app/tools.py` に関数 `make_quiz(lecture: int) -> str` を追加する
2. docstring に「いつ、何のために使うツールか」を書く（モデルはこれを読んで、使うかどうかを決める）
3. 用語集（`load_glossary()`）から、`lecture` が指定の回の用語を集め、1つ選ぶ（`random.choice` など）
4. 「○○の意味は？」という問題と、答え（その用語の `definition`）を文字列で返す（`json.dumps` など）
5. `app/agent.py` の `TODO(第3回 演習)` の場所で `agent.tool_plain(tools.make_quiz)` と登録する

`make_quiz(2)` の返り値の例：

```text
{"question": "「PEFT」の意味は？", "answer": "モデルの全パラメータではなく、…"}
```

### 5. make_quiz が呼ばれるか確かめる

```bash
uv run python -m app.agent --list-tools    # モデルに見えるツールの一覧（API キー不要）
uv run python -m app.agent --trace "第2回の内容から確認問題を1問出して"
uv run pytest -q
```

一覧に `make_quiz` と自分の docstring が出て、`[tool call] make_quiz({'lecture': 2})` のような行が出れば成功です。

`uv run pytest -q` は、API キーを使わずに、追加した `make_quiz` も含めて全部のツールをダミーの引数（`lecture=0` など）で呼び、エラーで落ちないかを確かめます。第0回は存在しないので、用語が見つからないときの処理を書いていないと失敗します。そのときは、用語が無い場合に分かりやすいメッセージを返すようにしましょう。

- 一覧に無い → `app/agent.py` で登録していない
- 一覧にはあるが呼ばれない → docstring に使う場面を具体的に書く。`INSTRUCTIONS` に「確認問題を求められたら make_quiz を使う」と足す

### 6. 提出して、Codespaces を停止する

`lectures/03/answer.md` を書き、`lec03` → 自分の fork の `main` へ PR を出します。**base repository が自分の fork になっていることを確認してください。**

```bash
git add -A
git commit -m "第3回 演習"
git push -u origin lec03
```

手順4が終わらなかった場合は、手順3までの結果で提出してかまいません。続きは同じブランチに push すれば PR に反映されます。

最後に、左下の「Codespaces」→ **Stop Current Codespace** で停止します。

## 宿題（どれか1つで完了）

基礎・実装・発展の3つのレベルから1つを選んで取り組みます。どれか1つに取り組めば完了です。

| レベル | 内容 |
|---|---|
| 基礎 | 演習で見た `app/agent.py` の `INSTRUCTIONS` や、`app/tools.py` のツールの docstring を書き換えます。同じ質問を `--trace` 付きで実行し、ツールの呼ばれ方や回答がどう変わるかを比べて記録します |
| 実装 | 学習の記録を `learning_log/` フォルダに保存するツール `save_learning_log` を作ります。保存は取り消しにくい操作なので、保存の前に利用者の確認を挟みます（Pydantic AI の `requires_approval=True`） |
| 発展 | 次のどちらかに取り組みます。(a) 演習のエージェントと同じ指示とツールを使い、エージェントを組み立てる部分だけを Google の ADK で書き直し、`adk run` で動かして、書き方や回答を比べます。(b) コーディングエージェントの Pi を Codespaces で動かし、公開されている Pi のシステムプロンプトと、自分のエージェントの `INSTRUCTIONS` を比べます |

提出は、演習と同じ `lectures/03/answer.md` の「宿題」欄に書きます。

### 基礎の進め方

演習の手順3で見た2か所のどちらかを、一度に1か所だけ変え、同じ質問を `--trace` 付きで実行して比べます。

- `app/agent.py` の `INSTRUCTIONS`（31行目付近）：エージェント全体への指示です
- `app/tools.py` の各ツールの docstring：ツールの説明文として、モデルに渡ります

たとえば、次のような変更が考えられます。ツールの呼ばれ方・回数・引数と、回答がどう変わったかを記録しましょう。

- `INSTRUCTIONS` から「必ず search_glossary で用語集を確認する」の行を消すと、検索せずに答えるようになるか
- `search_glossary` の docstring の「query には調べたい用語を1つだけ入れる」を「まとめて入れる」に変えると、検索の回数や引数がどう変わるか
- `INSTRUCTIONS` の「回答の最後に、関係する回（第N回）を示す」を別の指示（例：「最後に確認問題を1問出す」）に変えると、回答がどう変わるか

### 実装の進め方

1. `app/tools.py` に `save_learning_log` を作り、`app/agent.py` で `requires_approval=True` を付けて登録します
2. このツールをモデルが呼ぶと、実行は承認待ちで一度止まり、結果（`result.output`）として `DeferredToolRequests` が返ります。そのため、エージェントの `output_type` に `DeferredToolRequests` を加えます（加えないとエラーになります）

   ```python
   from pydantic_ai import Agent, DeferredToolRequests

   agent = Agent(instructions=INSTRUCTIONS,
                 output_type=[str, DeferredToolRequests])
   ```

3. CLI では、`result.output.approvals` の呼び出しごとに、保存してよいかを利用者に聞きます。その結果（`DeferredToolResults`）と、それまでの会話（`message_history=result.all_messages()`）を渡して、もう一度 `run_sync` を実行します

詳しくは、Pydantic AI の公式ドキュメント「Deferred Tools」の Human-in-the-Loop Tool Approval を参考にしてください：https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/

### 発展（a）の進め方：ADK で作り直す

演習のエージェントと同じ指示とツールを使い、エージェントを組み立てる部分だけを ADK で書き直します。

| 範囲 | 内容 |
|---|---|
| そのまま使う | `app/agent.py` の `INSTRUCTIONS` と、`app/tools.py` の `search_glossary`・`get_lecture_summary`（演習で `make_quiz` を作った人は `make_quiz` も） |
| 新しく書く | `adk_agent/glossary_agent/` フォルダに `agent.py`（下のコード）と `__init__.py`（中身は `from . import agent` の1行）を作ります |
| 作らなくてよい | `--trace` などのコマンドの機能、テスト、承認付きのツール。`app/` のファイルは変えません |
| 比べること | 書き方（指示とツールの渡し方）と、演習と同じ質問への回答の違い |

`adk_agent/glossary_agent/agent.py` の形：

```python
from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[...],  # 演習で使ったツール
)
```

動かすときは、リポジトリの直下で次を実行します。

```bash
PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
```

- `adk run` はターミナルで対話する方法です。質問を入力して Enter を押すと回答が返ります。終わるときは `exit` と入力します
- `uv run --with google-adk` は、講座の環境に ADK を一時的に足して実行する方法です。`pyproject.toml` や `uv.lock` は変わりません
- `PYTHONPATH=.` は、リポジトリ直下の `app` フォルダを読み込むために必要です
- API キーは、Codespaces secret の `GEMINI_API_KEY` がそのまま使われます
- 初回は ADK の取得に1分ほどかかります

演習と同じ質問を投げ、Pydantic AI 版との書き方の違いと、回答の違いを記録しましょう。

ADK は 2.0 で大きな変更がありました。Web 上の紹介記事などでは、変更に対応できていない古い情報が含まれることもあるため、公式ドキュメントの内容を参考に実装すると間違いが減ると思います。

- 公式ドキュメント：https://adk.dev/

### 発展（b）の進め方：Pi を Codespaces で動かす

Pi は、ファイルの書き換えやコマンドの実行を、確認を求めずに行うコーディングエージェントです。自分の PC ではなく、Codespaces の中で試してください。

1. **インストールする**：Codespaces のターミナルで次を実行します

   ```bash
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

2. **起動する**：ターミナルで `pi` と入力します
3. **モデルを設定する**：Pi の中で `/model` と入力し、Gemini のモデルを選びます。API キーは、Codespaces secret の `GEMINI_API_KEY` がそのまま使われます
4. **比べる**：Pi のシステムプロンプトは、公開リポジトリ https://github.com/earendil-works/pi の `packages/coding-agent/src/core/system-prompt.ts` にあります。自分の `INSTRUCTIONS` と比べ、何が書かれていて、何が書かれていないかを見てみましょう

- Pi の公式ドキュメント：https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## 参考

- Pydantic AI: https://pydantic.dev/docs/ai/
- ADK: https://adk.dev/
