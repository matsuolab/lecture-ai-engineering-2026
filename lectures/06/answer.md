# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 versioning overview'})
- 気づき・疑問：同じエージェントでも質問内容によって異なるMCPツールが呼び出されることを確認できた。ツール呼び出しの履歴（trace）を見ることで、エージェントがどのように回答を生成しているか理解しやすかった。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：
  app/mcp_server.py に get_lecture_summary ツールを追加した。
  その後、--list-tools でツール一覧を確認し、「第2回では何を学びますか？」という質問を実行してツールが呼び出されることを確認した。
  また、uv run pytest -q を実行してテストがすべて通ることを確認した。
- 結果：
 glossary_get_lecture_summary がツール一覧に追加された。
  質問時に [tool call] glossary_get_lecture_summary({'lecture': 2}) が表示され、自動的に新しいツールが利用された。
  テストは 21 passed ですべて成功した。
- 気づき・疑問：
  MCPではサーバー側でツールを追加するだけで、エージェント側のコードを変更しなくても自動的に新しいツールが認識されることが分かった。
  また、モデルが質問内容を見て適切なツールを選択して呼び出していることを trace から確認できた。
  実際のシステムでは、ツール数が増えたときにモデルはどのような基準でツールを選択しているのか気になった。