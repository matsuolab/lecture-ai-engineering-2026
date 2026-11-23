# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前: `glossary_search_glossary`
- STEP 2 の [tool call]: `glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]: `fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
- STEP 4 の [tool call]: `aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'})`
- 気づき・疑問：


## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->
- **取り組んだレベル**: 基礎
- **やったこと**:
  `app/mcp_server.py` に `server.tool()(tools.get_lecture_summary)` を1行追加し、用語集MCPサーバーから `get_lecture_summary` ツールを公開した。エージェント側（`app/mcp_agent.py`、`app/mcp_servers.json`）は変更せず、`--list-tools` でのツール追加と `--trace` 付き質問での呼び出し、および `uv run pytest -q` の全テスト通過（22 passed）を確認した。
- **結果**:
  `--list-tools` の一覧が7個から8個に増え、`glossary_get_lecture_summary` が追加された。「第2回では何を学びますか？」の質問に対して `[tool call]` で `glossary_get_lecture_summary({'lecture': 2})` が呼び出され、第2回（ファインチューニングとLoRA）の講義内容に関する回答が得られた。`uv run pytest -q` も全22件通過した。
- **気づき・疑問**:
  エージェントが起動時にMCPサーバーへ `tools/list` を問い合わせて公開ツール一覧を動的に取得するため、サーバー側の公開設定を変更するだけでエージェント側のコードや設定を修正せずに利用できる点（ツールとエージェントの分離による保守性）を実感した。
