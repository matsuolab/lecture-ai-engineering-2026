# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：`search_materials` / `make_quiz`（`app.agent`、第3回までのエージェント内蔵ツール）と `glossary_search_glossary` / `glossary_get_lecture_summary` / `glossary_make_quiz`（`app.mcp_agent`、MCPサーバー経由・宿題で2つ追加済みの状態）
- STEP 2 の [tool call]：`glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]：`fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
- STEP 4 の [tool call]：`aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング'})`（ほか `{'topics': ['general'], 'search_phrase': 'S3 バージョニングとは'}`、`{'search_phrase': 'Using versioning in S3 buckets'}` と合計3回呼び出し）
- 気づき・疑問：`command` 型のサーバーは自分の環境で起動するので送られる情報はツール実行の範囲に留まる一方、`url` 型（aws）では質問内容そのものが外部の提供者に送られる。導入前に提供元と既定動作（`--allow-private-ips` 等の保護設定）を確認する運用が必要だと感じた。また、公開ツール数が `command` 型では関数名ベースの名前（`glossary_search_glossary`）、`url` 型では `aws_aws___search_documentation` のようにサーバー名を含む命名になるため、名前の衝突を避けつつどのサーバーのツールか一目で分かる設計になっている。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：実装（基礎も実施）
- やったこと：
  - 基礎：`app/mcp_server.py` の TODO の下に `server.tool()(tools.get_lecture_summary)` を1行追加し、`glossary_get_lecture_summary` を公開した
  - 実装：第3回で作った `make_quiz` も `server.tool()(tools.make_quiz)` で公開し、`glossary_make_quiz` として使えるようにした。あわせて `app/tools.py` の `make_quiz` を修正し、存在しない回が指定されたときに「クイズを作れる回は第1〜6回です」と有効な範囲を返すようにした（変更前は「用語はまだありません」のみで、次に何を聞けばよいか分からなかった）
  - 変更ファイルは `app/mcp_server.py` と `app/tools.py` の2つ（`git status` で確認済み）。エージェント側（`mcp_servers.json` / `mcp_agent.py`）は演習 STEP 3・4 のサーバー追加以外は変更していない
- 結果：
  - `uv run python -m app.mcp_agent --list-tools` で一覧に `glossary_get_lecture_summary` と `glossary_make_quiz` が増えた（エージェント側の設定・コードは変えていないのに使えるようになった）
  - `--trace "make_quiz ツールを使って、第5回のクイズを作って"` で `[tool call] glossary_make_quiz({'lecture': 5})` → `[tool return] 第5回の用語は用語集にまだありません。クイズを作れる回は第1〜6回です。` が返り、モデルは「第5回は用語集に登録されていないため作成できません。第1〜6回から指定してください」と範囲を含めて案内した。エラーメッセージの文字列はそのまま tool return としてモデルに渡り、モデルが利用者向けに言い換えて回答することを確認した
  - `uv run pytest -q` で全21件通過
- 気づき・疑問：範囲外の引数に対して「なぜダメか＋何ならできるか」を返すと、モデルが次の行動（有効な回の案内）まで一貫して導けることが分かった。エラーメッセージもプロンプトの一部だと実感した。一方で「第99回のクイズを作って」とだけ聞くと、モデルはツールを呼ばず「第99回は存在しない」と即答してしまい、ツールのエラーメッセージが試されないケースがあった（ツール名を明示して呼ばせる必要があった）。エラーパスを確実に通したいときは、質問文の書き方も含めて検証設計が要ると感じた。
