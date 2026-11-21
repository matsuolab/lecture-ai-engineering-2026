# 第6回 演習・宿題：MCP サーバーをエージェントから使う

## この回のゴール

MCP サーバーのツールを、エージェントから使います。できるようになることは 3 つです。

- 自分で作った MCP サーバー（第3回の用語集のツール）を、エージェントから使える
- モデルに渡っているツールの名前・説明文・引数を、自分で表示して読める
- ほかの人が作った MCP サーバーを、設定ファイルに書き足すだけで使える

演習は、自分の fork の GitHub Codespaces で行います。Gemini API のキーは、第1回で登録したものを使います。

## MCP サーバーの使い方：3 つの場合

MCP サーバーの使い方は、サーバーを自分で作るか、どこで動かすかで、3 つに分けられます。この演習では、3 つを順に試します。

| | ① 自分で作ったサーバーを立てる | ② 公開されているサーバーを使う | ③ 外部で動くサーバーに接続する |
|---|---|---|---|
| つなぎ方 | エージェントが、自分の環境にコマンドで起動します | `uvx` が取得して、自分の環境に起動します | すでに動いているサーバーに接続します |
| 試す STEP | STEP 1・2（用語集サーバー） | STEP 3（fetch サーバー） | STEP 4（AWS Knowledge サーバー） |
| 設定の書き方 | `"command": "uv"` | `"command": "uvx"` | `"url": "https://…"` |

設定に `command` があれば自分の環境で起動し、`url` があれば外部で動くサーバーに接続します。

## 第6回で使うファイル

演習で書き換えるファイルは、設定ファイルの 1 つです。ほかは、実行するか、読むだけです。

| ファイル | 何をするファイルか | 第6回ですること |
|---|---|---|
| [app/tools.py](../../app/tools.py) | ツールの関数が入っています。使うのは、第3回で作った `search_glossary` と `get_lecture_summary` です | 読むだけです |
| [app/mcp_server.py](../../app/mcp_server.py) | `app/tools.py` の関数を、MCP のツールとして公開するサーバーです | 読むだけです（宿題の基礎で 1 行書き足します） |
| [app/mcp_servers.json](../../app/mcp_servers.json) | エージェントがどの MCP サーバーを使うかを書く、設定ファイルです | STEP 3 と STEP 4 で、サーバーを書き足します |
| [app/mcp_agent.py](../../app/mcp_agent.py) | 設定ファイルのサーバーに接続し、そのツールを使うエージェントです | コマンドで実行します |
| [app/agent.py](../../app/agent.py) | 第5回までの演習で使ってきたエージェントです | STEP 1 でツールの一覧を表示します。書き換えません |

## 演習（30分）

準備から STEP 5 までを、約 23 分で行います。

### 準備：lec06 ブランチを作る（約2分）

第6回の更新を自分の fork に取り込み、作業用の `lec06` ブランチを作ります。

1. 自分の fork のページで **Sync fork → Update branch** を押します（すでに最新の場合は、押すものはありません）
2. Codespaces のターミナルで、次のコマンドを上から順に実行します

```bash
git switch main
git pull --no-rebase
git switch -c lec06
uv sync --frozen
```

3. 最後に `ls app/mcp_agent.py` を実行し、ファイル名が表示されることを確認します

- `git switch main` で止まるときは、前の回のブランチに変更が残っています。commit してから、もう一度実行します
- `a branch named 'lec06' already exists` と出るときは、`git switch lec06` で切り替えます
- `git pull --no-rebase` で `CONFLICT` と出るときは、`git merge --abort` で元に戻し、下の手順で始めます（自分の変更は消えません）

#### 前の回までの作業が終わっていない場合

第6回の開始時点（`lec06-start` タグ）から始めます。次のコマンドを上から順に実行します。

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec06-start
git switch -c lec06 lec06-start
uv sync --frozen
```

Sync fork で衝突の表示が出た場合も、こちらで始めます。「Discard commits」は押しません（自分のコミットが消えます）。

### STEP 1：自分で作ったサーバーのツールを表示する（約4分）

ゴール：エージェントが用語集サーバーを起動し、そのツールがモデルに渡ることを確かめる

```bash
uv run python -m app.agent --list-tools
uv run python -m app.mcp_agent --list-tools
```

どちらのコマンドも、API キーがなくても動きます。

1. 1 つ目は、第5回までのエージェントのツールです。`search_materials` が表示されます
2. 2 つ目の 1 行目は、エージェントが用語集サーバーをコマンドで起動したことを示します。その下が、サーバーから受け取ったツールです
3. 2 つを比べます。どちらも、名前・説明文・引数が並んでいます。モデルには同じ形で渡ります

2 つ目のコマンドの表示：

```text
[server] glossary: コマンドで起動（uv run python -m app.mcp_server）
モデルに見えているツール: 1 個

[glossary_search_glossary]
  講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

  AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
  答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
  引数: {"query": {"title": "Query", "type": "string"}}
```

MCP サーバーのツールは、「サーバー名」「`_`」「ツール名」の順につないだ名前になります。`glossary_search_glossary` の場合、`glossary` は設定ファイルに書いたサーバー名で、`search_glossary` は `app/tools.py` の関数の名前です。複数のサーバーに同じ名前のツールがあっても、区別できます。

### STEP 2：エージェントに質問して、ツールの呼び出しを見る（約4分）

ゴール：質問に答えるとき、MCP サーバーのツールが呼ばれていることを確かめる

```bash
uv run python -m app.mcp_agent --trace "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
```

第3回の演習と同じ質問です。表示の `--- trace ---` より下で、次の 3 つを確かめます。

1. `[tool call]` の行に、`glossary_search_glossary` と、モデルが決めた引数が出ています
2. `[tool return]` の行に、MCP サーバーが返した用語集の内容が出ています
3. `[usage]` の行の「モデル応答」は 2 回以上です。1 回目でツールを呼び、2 回目でその結果を読んで答えるためです

第3回では、エージェントがこの関数を直接呼びました。第6回では、MCP サーバーが関数を呼び、結果をエージェントに返しています。

### STEP 3：公開されているサーバーを取得して使う（約5分）

ゴール：Web ページを取得する fetch サーバーを設定に書き足し、エージェントから使えることを確かめる

1. `app/mcp_servers.json` を開き、次のとおり `"fetch"` から始まる 4 行を書き足します。`glossary` の `}` のあとに `,` を付けます

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"]
    }
  }
}
```

2. 1 つ目のコマンドで、`[server] fetch: コマンドで起動` と表示され、一覧に `fetch_fetch` が増えていることを確認します
3. 2 つ目のコマンドで質問し、`[tool call]` の行に `fetch_fetch` と URL が出ることを確認します

```bash
uv run python -m app.mcp_agent --list-tools
uv run python -m app.mcp_agent --trace "https://modelcontextprotocol.io/ の冒頭を日本語で3行に要約して"
```

- `uvx` は、公開されているプログラムを取得して実行するコマンドです。fetch サーバーは、自分の Codespaces の中で動きます。1 つ目のコマンドは、初回だけ 10 秒ほどかかります
- `==2026.11.11` は、使う版の指定です。外部のサーバーは更新で動きが変わることがあるので、この講座では版を固定します
- `--no-readability-js` は、ページ本文の取り出しを Python だけで行う指定です
- `fetch_fetch` の説明文は英語です。サーバーの作者が書いた説明文が、そのままモデルに渡ります

### STEP 4：外部で動くサーバーに接続する（約5分）

ゴール：AWS が動かしている MCP サーバーに URL で接続し、エージェントから使えることを確かめる

1. `app/mcp_servers.json` を開き、`fetch` の `}` のあとに `,` を付け、`"aws"` の 1 行を書き足します

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"]
    },
    "aws": {"url": "https://knowledge-mcp.global.api.aws"}
  }
}
```

2. 1 つ目のコマンドで、`[server] aws: URL に接続` と表示され、`aws_` で始まるツールが増えていることを確認します
3. 2 つ目のコマンドで質問し、`[tool call]` の行に `aws_` で始まるツールが出ることを確認します

```bash
uv run python -m app.mcp_agent --list-tools
uv run python -m app.mcp_agent --trace "AWSのドキュメントを検索して、Amazon S3 のバージョニングを2行で説明して"
```

1 つ目のコマンドの表示（はじめの 3 行）：

```text
[server] glossary: コマンドで起動（uv run python -m app.mcp_server）
[server] fetch: コマンドで起動（uvx mcp-server-fetch==2026.11.11 --no-readability-js）
[server] aws: URL に接続（https://knowledge-mcp.global.api.aws）
```

STEP 3 までとの違いは、`aws` に起動するコマンドがないことです。サーバーは AWS が動かしていて、エージェントは URL に接続します。質問の内容は AWS に送られます。

### 補足：既製の外部ツールを足す前に確認すること

STEP 3 と STEP 4 では、設定ファイルに数行足すだけで、ほかの人が作ったサーバーのツールが使えるようになりました。足す前に、次の 2 つを確認して把握します。

1. **信頼できる MCP サーバーか**：誰が提供しているか、ソースコードがどこにあるかを確認します。fetch の提供元は MCP のリポジトリ、AWS Knowledge の提供元は AWS です。出所の分からないサーバーは、設定ファイルに書きません
2. **どのようなリスクがあるか**：README や公式ページの注意書きと、既定の動作を読みます。fetch の README には、内部の IP アドレスにアクセスでき、セキュリティ上のリスクになり得る、と書かれています。外部で動くサーバーでは、ツールに渡した内容が提供者に送られます

fetch サーバーは、内部の情報と、自動取得を断っているサイトを守るために、既定では次のように動きます。

| 既定の動作 | オプションを付けたとき |
|---|---|
| 非公開のアドレス（`localhost` や社内のネットワーク）からは、取得しません | `--allow-private-ips` を付けると、取得します |
| サイトが `robots.txt` で自動取得を禁止しているページは、取得しません | `--ignore-robots-txt` を付けると、取得します |
| それ以外のページは、どのホストからも取得します | `--allowed-hosts` で、取得先のホストを絞れます |

MCP のリポジトリが提供するサーバーにも、利用上のリスクが書かれています。提供元とリスクの記載を確認してから足します。

### STEP 5：提出して、Codespaces を停止する（約3分）

ゴール：結果を `answer.md` に書いて PR を出し、Codespaces を停止する

1. `lectures/06/answer.md` を開き、STEP 1 のツールの名前と、STEP 2〜4 の `[tool call]` の行（呼ばれたツールの名前と引数）を貼り付けます
2. commit と push をします

```bash
git add -A
git commit -m "第6回 演習"
git push -u origin lec06
```

3. GitHub で、`lec06` から自分の fork の `main` への PR を作ります。base repository が自分の fork になっていることを確認します
4. 画面左下の「Codespaces」を押し、「Stop Current Codespace」を選びます

`answer.md` に書く例：

```text
- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://…'})
- STEP 4 の [tool call]：aws_…（表示された行を、そのまま貼り付けます）
```

STEP 4 まで終わらなかった場合は、終わったところまでを書いて提出し、続きは同じブランチに push します。

### うまくいかないとき

解決しないときは、チャットで、症状と表示されたメッセージを知らせてください。

| 症状 | 対処 |
|---|---|
| `No module named app.mcp_agent` と出る | 第6回の更新が、まだ自分のブランチに入っていません。準備の手順で `main` を更新してから、`git switch lec06`、`git merge main` の順に実行します |
| 「app/mcp_servers.json を読めませんでした」と出る | 設定ファイルの書き方に誤りがあります。表示された行の近くで、サーバーとサーバーの間に `,` があるか、最後のサーバーのあとに余分な `,` がないかを確認します |
| 「MCP サーバーに接続できませんでした」と出る | `app/mcp_servers.json` に書いたコマンド名や URL に、誤りがないかを確認します |
| URL を渡しても fetch が呼ばれない | `app/mcp_agent.py` の `INSTRUCTIONS` に「URL を渡されたら fetch で内容を読む」という 1 行を書き足します |
| `aws` を足したあと、接続できないと出る | URL に書き間違いがないかを確認します。利用回数の制限のこともあるので、1 分ほど待ってから、もう一度実行します |
| 「レート制限に達しました」と出る | 1 分ほど待ってから、同じコマンドをもう一度実行します |
| `GEMINI_API_KEY` が見つからないと出る | 第1回の手順で Codespaces secret を登録し、Codespaces を再起動します |

## 宿題（どれか1つで完了）

基礎・実装・発展の 3 つのレベルから 1 つを選びます。どれか 1 つに取り組めば完了です。

| レベル | 内容 |
|---|---|
| 基礎 | 演習で使った用語集の MCP サーバーに、ツールをもう 1 つ公開します（`get_lecture_summary`）。書き換えるのはサーバー側の `app/mcp_server.py` だけです。エージェント側を変えなくても、一覧にツールが増え、質問で呼ばれることを確かめます |
| 実装 | MCP サーバーに、自分でツールを追加します（第3回で作った `make_quiz`。なければ新しいツール）。引数が範囲外のときに分かりやすいメッセージを返すようにし、そのメッセージがモデルにどう伝わるかを確かめます |
| 発展 | 自分が使っているソフトウェア（Claude Code、Codex、Gemini CLI など）を 1 つ選び、MCP サーバーの設定方法を公式ドキュメントで調べます。特に使っているものがない場合は、VS Code を調べます。調べた設定方法を、演習で使った `app/mcp_servers.json` と比べます |

### 基礎の進め方

書き換えるのは、サーバー側のファイル 1 つだけです。エージェント側の設定とコードは変えません。

| | ファイル |
|---|---|
| サーバー側：書き換えます | `app/mcp_server.py`（公開するツールを決めるファイルです） |
| エージェント側：変えません | `app/mcp_servers.json`（接続先の設定）、`app/mcp_agent.py`（エージェント本体） |

1. `app/mcp_server.py` を開き、`TODO` の行の下に、次の最後の 1 行を書き足して保存します

   ```python
   server.tool()(tools.search_glossary)

   # TODO(宿題・基礎): get_lecture_summary も公開しよう
   server.tool()(tools.get_lecture_summary)
   ```

2. `git status` で、変更されたファイルが `app/mcp_server.py` だけであることを確認します（演習の変更を STEP 5 で commit してあることが前提です）
3. エージェント側を変えずに、一覧に `glossary_get_lecture_summary` が増えたことを確認します
4. 「第2回では何を学びますか？」と質問し、書き足したツールが呼ばれることを確認します
5. `uv run pytest -q` を実行し、テストがすべて通ることを確認します

```bash
git status
uv run python -m app.mcp_agent --list-tools
uv run python -m app.mcp_agent --trace "第2回では何を学びますか？"
uv run pytest -q
```

エージェントは、起動するたびに、公開されているツールの一覧をサーバーに問い合わせます。そのため、エージェント側を変えなくても、足したツールが使えます。

### 実装の進め方

1. 第3回で作った `make_quiz` を、`app/mcp_server.py` で公開します（基礎と同じ書き方です）。`make_quiz` がない場合は、新しいツールを作ります。`app/mcp_server.py` に関数を書き、その上の行に `@server.tool()` を付けると、MCP のツールになります
2. 引数が範囲外のとき（例：存在しない回）に、分かりやすいメッセージを `return` で返すようにします
3. 範囲外になる質問をして、そのメッセージがモデルにどう伝わるかを `--trace` で確認します

```bash
uv run python -m app.mcp_agent --trace "第99回のクイズを作って"
```

- `return` で返したメッセージは、`[tool return]` の行に出て、そのままモデルに渡ります
- 例外（`raise`）にした場合は、`[tool error]` の行に出ます。モデルに渡る内容が `return` のときとどう違うかを、比べてみてください

### 発展の進め方

自分が使っているソフトウェアで、MCP サーバーをどう設定するのかを調べ、演習の設定ファイルと比べます。調べて比べる課題です。ソフトウェアを新しく契約したり、インストールしたりする必要はありません。

1. 自分が使っているソフトウェアを 1 つ選びます（例：Claude Code、Codex、Gemini CLI）。特に使っているものがない場合は、VS Code を調べます
2. そのソフトウェアの公式ドキュメントで、MCP サーバーの設定方法を調べます
3. 演習で使った `app/mcp_servers.json` と比べ、違いを書きます

調べることは、次の 4 つです。

| 調べること | 見るところ |
|---|---|
| 設定を書く場所 | ファイルの名前と置き場所（または、登録するコマンド） |
| コマンドで起動する書き方 | 演習の `"command"` にあたる部分 |
| URL で接続する書き方 | 演習の `"url"` にあたる部分 |
| 有効になる範囲 | そのプロジェクトだけか、すべてのプロジェクトか |

調べた日付と、参照した公式ドキュメントの URL も書きます。設定方法は変わることがあります。

### 宿題の提出

演習と同じ `lectures/06/answer.md` の「宿題」欄に、取り組んだレベル、やったこと、結果、気づき・疑問を書き、同じ `lec06` ブランチに push します。AI ツールは使ってかまいません。自分で確かめたことを書いてください。

## 参考

- MCP の公式サイト: https://modelcontextprotocol.io/
- Pydantic AI の MCP クライアント: https://pydantic.dev/docs/ai/mcp/client/
- MCP の Python SDK（サーバーの書き方）: https://github.com/modelcontextprotocol/python-sdk
- 公開されている MCP サーバー: https://github.com/modelcontextprotocol/servers
- fetch サーバーの README: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch
- AWS Knowledge MCP Server: https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server
- VS Code で MCP サーバーを使う（発展で VS Code を調べる場合）: https://code.visualstudio.com/docs/agent-customization/mcp-servers
