# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})
- 気づき・疑問：MCPサーバーから渡されたツールには、サーバー名とツール名が組み合わされて
「glossary_search_glossary」のような名前になることが分かった。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：app/mcp_server.py にget_lecture_summary を MCP のツールとして公開する1行を追加した。
  エージェント側の設定やコードは変更せず、サーバー側だけを変更した。
- 結果：ツール一覧に glossary_get_lecture_summary が増え、「第2回では何を学びますか？」への回答時にツールが呼ばれることを確認した。
- 気づき・疑問：エージェント側のコードを変更せず、MCPサーバーにツールを追加するだけでエージェントから利用できることを確認できた。
