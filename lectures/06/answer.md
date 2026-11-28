# 第6回 解答

## 演習

- **STEP 1 のツールの名前：**
  - 第5回までの直接登録方式：`search_glossary`、`get_lecture_summary`
  - MCPサーバー経由：`glossary_search_glossary`
  - MCPサーバー経由では、サーバー名のプレフィックスが付いたツール名が表示された。

- **STEP 2 の [tool call]：**

  `glossary_search_glossary({'query': 'LoRA QLoRA'})`

  LoRAとQLoRAの違いを質問したところ、MCPサーバー経由で用語集が検索され、正しい説明が得られた。モデル応答は2回であった。

- **STEP 3 の [tool call]：**

  `fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`

  公開されているfetchサーバーを`app/mcp_servers.json`に追加したところ、ツールが1個増えた。MCP公式サイトの冒頭を取得し、日本語で3行に要約できた。

- **STEP 4 の [tool call]：**

  `aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング'})`

  `aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'What is S3 Versioning'})`

  AWS Knowledge MCPサーバーをURLで追加したところ、AWSのツールが5個増えた。Amazon S3のバージョニングについて、外部の公式ドキュメントを検索して回答できた。

- **気づき・疑問：**

  MCPサーバーの設定ファイルに接続先を追加するだけで、エージェント側のコードを変更せずに利用可能なツールを増やせることを確認した。自作サーバーと公開サーバーはCodespaces内で起動する一方、AWSサーバーにはURLで接続するという違いを理解した。また、外部MCPサーバーの説明文や取得内容には信頼できない指示が含まれる可能性があるため、提供元や権限の確認が重要だと感じた。

## 宿題

- **取り組んだレベル：** 基礎

- **やったこと：**

  `app/mcp_server.py`のTODOコメントの下に、次の1行を追加した。

  `server.tool()(tools.get_lecture_summary)`

  `app/mcp_agent.py`は変更せず、MCPサーバー側だけで新しいツールを公開した。

- **結果：**

  `uv run python -m app.mcp_agent --list-tools`を実行すると、新しい`glossary_get_lecture_summary`が一覧に追加された。利用可能なツール数は、演習STEP 4終了時の7個から8個に増加した。

  続いて「第2回では何を学びますか？」と質問したところ、次のツール呼び出しを確認できた。

  `glossary_get_lecture_summary({'lecture': 2})`

  MCPサーバーから第2回「ファインチューニングとLoRA」の要点が返され、エージェントはその内容をもとに回答した。

  また、`uv run pytest -q`を実行した結果、**21件すべてのテストが成功した（21 passed in 4.42s）。**

- **気づき・疑問：**

  MCPサーバーにツールを登録するだけで、エージェントが起動時に新しいツールを認識し、適切な質問に応じて呼び出せることを確認した。第3回のようにエージェントへ関数を直接登録する方法と比較し、MCPではツールの公開と利用を分離できることが理解できた。今後は、公開特許文献の検索など知財業務に関係する独自ツールをMCPサーバーに追加し、複数のAIエージェントから共通利用する仕組みにも挑戦したい。
