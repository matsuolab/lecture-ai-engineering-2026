# 第6回 解答

## 演習

- `--list-tools` で見えたツール名と、第3回（`--mcp` なし）との違い：glossary_search_glossary と glossary_get_lecture_summary の2つのツールが表示された。 第3回ではツールをエージェントへ直接登録していたが、第6回ではMCPサーバー経由でツールが公開され、エージェントはMCPサーバーからツール一覧を取得して利用していた。
- `--mcp --trace` で見えたツール呼び出し（ツール名と引数）と、`requests` の回数：glossary_get_lecture_summary({"lecture": 2}) が呼び出された。 requests は 2 回だった。
- MCP サーバーに公開したツールと、その説明文：公開したツールは get_lecture_summary である。 説明文は 「指定した回（1始まりの整数）の講義の要点を返す。『第3回では何を学ぶ？』のように、回の内容や関係を聞かれたときに使う。」 であった。
- fetch サーバーを足したときのツール呼び出し（ツール名と引数）： 今回は基礎課題を選択したため fetch サーバーの追加は実施していない。その代わりに、MCPサーバーへ get_lecture_summary を追加し、glossary_get_lecture_summary({'lecture': 2}) が呼び出されることを確認した。

## 宿題

- 取り組んだレベル：基礎
- やったこと：app/mcp_server.py に server.tool()(tools.get_lecture_summary) を追加し、講義要約を返すツールを MCP サーバー経由で公開した。

その後、 uv run python -m app.agent --mcp --list-tools を実行し、公開されたツール一覧を確認した。

さらに、

uv run python -m app.agent --mcp --trace "第2回では何を学びますか？"

を実行し、実際にツールが呼び出されることを確認した。
- 結果：--list-tools の結果として、

glossary_search_glossary
glossary_get_lecture_summary
の2つのツールが表示された。

また、--trace 実行時には

glossary_get_lecture_summary({'lecture': 2})

が呼び出され、第2回の講義内容をまとめた回答が生成された。

モデル応答回数（requests）は2回だった。
- 気づき・疑問：エージェント本体のコードを変更しなくても、MCPサーバー側でツールを公開するだけで機能を拡張できることが分かった。また、ツールの名前や説明文がモデルの判断に大きく影響することを理解できた。MCPを利用することで、同じツールを複数のエージェントやクライアントから再利用できる点が便利だと感じた。

