# 第6回 解答

## 演習

- STEP 1 のツールの名前：
  - search_materials
  - search_glossary
  - get_lecture_summary
  - make_quiz
  - glossary_search_glossary

- STEP 2 の [tool call]：
  - [tool call]   glossary_search_glossary({'query': '3レベル'})

- STEP 3 の [tool call]：
  - [tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})

- STEP 4 の [tool call]：
  - [tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
  - [tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Using versioning Amazon S3'})

- 気づき・疑問：
  - MCPサーバーを設定ファイルに追加すると、エージェントが利用できるツールが増えることが分かった。
  - 自作の用語集、Webページ取得、AWS公式ドキュメント検索を同じエージェントから利用できた。

## 宿題

- 取り組んだレベル：基礎
- やったこと：app/mcp_server.py に get_lecture_summary をMCPツールとして登録した。
- 結果：glossary_get_lecture_summary が追加され、第2回の講義要約を取得できた。pytestは22件すべて合格。
- 気づき・疑問：既存のPython関数を1行登録するだけで、MCP経由で利用できることが分かった。
