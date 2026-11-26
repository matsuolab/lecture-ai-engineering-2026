# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：[tool call]   glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 versioning overview'})
- 気づき・疑問：設定ファイル（app/mcp_servers.json）にサーバーを記述するだけで、ローカルの自作サーバー（stdio）も外部の公開サーバー（uvxやStreamable HTTP）も同じ仕組みで動的にロードでき、ツール名にプレフィックスが付与されることで衝突が防げる点が理解できた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：app/mcp_server.py に `server.tool()(tools.get_lecture_summary)` を追加し、`get_lecture_summary` を MCP サーバーのツールとして公開した。
- 結果：`--list-tools` に `glossary_get_lecture_summary` が追加され、「第2回では何を学びますか?」の質問に対して `[tool call]   glossary_get_lecture_summary({'lecture': 2})` が呼び出され、第2回の講義概要が正しく回答されることを確認した。
- 気づき・疑問：エージェント本体（app/mcp_agent.py）のコードを変更しなくても、MCP サーバー側でツールを公開して指示文と組み合わせるだけで、エージェントが自律的に適切なツールを選択して呼び出せることを確認できた。
