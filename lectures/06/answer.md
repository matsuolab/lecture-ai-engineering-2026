# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary

- STEP 2 の [tool call]：
glossary_search_glossary({'query': '3レベル'})

- STEP 3 の [tool call]：
 fetch_fetch({'url': 'https://modelcontextprotocol.io/'})

- STEP 4 の [tool call]：
 aws_aws___search_documentation({'search_phrase': 'Amazon S3 versioning overview', 'topics': ['general']})

- 気づき・疑問：
・MCPサーバーがローカルで動いていてもAWS上で動いていても、エージェントからは同じようにツールとして利用できることが分かった。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎 
- やったこと：
 app/mcp_server.py に server.tool()(tools.get_lecture_summary) を追加し、get_lecture_summary を MCP ツールとして公開した。

- 結果：
 uv run python -m app.mcp_agent --list-tools を実行し、従来の glossary_search_glossary に加えて glossary_get_lecture_summary が表示されることを確認した。

- 気づき・疑問：
 ・サーバー側でツールを公開するだけで、エージェント側を変更しなくても利用可能なツール一覧に自動的に追加される。
