# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前： `search_materials`, `make_quiz`
- STEP 2 の [tool call]： `[tool call] glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]： `[tool call] fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
- STEP 4 の [tool call]：
  - `[tool call] aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})`
  - `[tool call] aws_aws___search_documentation({'topics': ['general'], 'search_phrase': '"Using versioning" Amazon S3 overview'})`
  - `[tool call] glossary_search_glossary({'query': 'Amazon S3'})`
- 気づき・疑問： MCPサーバーを増やすとツールの説明文だけで入力トークンが増える（715→15,879 tokens）。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：発展
- やったこと：vscodeのMCP サーバーの設定方法を調べて比べる
- 結果：設定ファイルはmcp.jsonで、プロジェクト単位の.vscode/mcp.jsonと、ユーザー全体の設定がある。コマンド起動にはcommandとargs、URL接続にはurlを使用する。演習のmcpServersに対し、VS Codeでは最上位キーにserversを使う点が異なる。
- 気づき・疑問：MCPの基本的な設定方法は共通しているが、ソフトウェアによって設定ファイルの場所や記述形式が異なると分かった。特に、mcpServersとserversを使い分ける必要がある。通信方式のtypeを省略した場合の動作について、さらに確認したい。