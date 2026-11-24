# 第6回 解答

## 演習

- STEP 1 のツールの名前：glossary_search_glossary（比較：第5回までの app.agent は search_materials と make_quiz の 2 個）
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：
  - aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})
  - aws_aws___search_documentation({'search_phrase': 'Using versioning S3 developer guide overview', 'topics': ['general']})
- 気づき・疑問：
  - fetch_fetch の説明文は英語で、「インターネットにアクセスできるようになった」とモデルに語りかける文が入っていた。説明文はモデルへの指示として働くので、信頼できる提供元のサーバーだけを使う必要がある。

  - fetch は、ページを取得する前に robots.txt を確認していた（ログに出た HTTP リクエストで分かる）
  - AWS のサーバーを足すとツールが 5 個増え、説明文も長いため、STEP 4 の入力は 11,064 トークンになった（STEP 2 は 715、STEP 3 は 2,230）。サーバーを足すほど、毎回の入力トークンが増える
  - STEP 4 では、日本語で 1 回検索したあと、英語で検索し直していた。質問の内容は AWSに送られる

## 宿題

- 取り組んだレベル：基礎
- やったこと：app/mcp_server.py の TODO の下に server.tool()(tools.get_lecture_summary) の 1 行を足した。git status で、変更がこのファイルだけであることを確認した。エージェント側（mcp_servers.json、mcp_agent.py）は変えていない
- 結果：
  - ツール一覧が 7 個から 8 個になり、glossary_get_lecture_summary が増えた。説明文と引数（lecture: integer）は、tools.py の関数の docstring と型から作られていた
  - 「第2回では何を学びますか？」に対して glossary_get_lecture_summary({'lecture': 2}) が呼ばれ、第2回の要点（ファインチューニング、SFT、LoRA など）に沿って回答した。入力 5,942 トークン、モデル応答 2 回
  - uv run pytest -q：23 passed
- 気づき・疑問：
  - エージェントは起動のたびにサーバーへツールの一覧を問い合わせるので、サーバー側を変えるだけでツールを増やせる。ツールを提供する側と使う側を分けて変更できるのが MCP の利点だと分かった
  - サーバー側の変更がエージェントにそのまま伝わる。外部のサーバーでツールや説明文が変わると、エージェントの挙動も変わるので、版の固定が大事
