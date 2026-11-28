# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：[tool call]   glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
- 気づき・疑問：mcp_servers.jsonへの新しいmcpサーバーを追加するには、前の定義の下にカンマを追加したりと、技術者でないと難しいところがあり、この辺りは、GUIで出来るようにするか、CSVで定義して、行だけ追加できるようにしてもらった方が扱いやすいかと思いました。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル： 発展
- やったこと：講座で使ったAWSのMCP ServerをcodespaceのVS Code側の設定としても追加し、VS Code側のMCP Serverを呼び出すAgentを別途作成して実行。
- 結果：講座の `mcp_agent.py` は `app/mcp_servers.json` を読み、`command` と `args` でサーバーを起動するか、`url` で稼働中のサーバーに接続。この設定は講座のエージェントに適用される。

今回の `mcp_agent2.py` は、VS Codeで作成したリポジトリ直下の `.mcp.json` を読み、`aws` の `url` を使ってAWSのMCPサーバーに直接接続。`"type": "http"` はCopilot向けの指定で、`mcp_agent2.py` の対応範囲は `aws` のURL接続。同じファイルが、Copilotではワークスペース設定、自作プログラムでは接続先の設定として使われる。
- 気づき・疑問：ガバナンスの観点からは、MCPの定義は1箇所に一元管理して欲しいが、アプリ側で定義してアクセスも可能で、その設定は、VS Codeの設定でも確認出来ないとなると、標準化の観点からは不都合を感じた。
