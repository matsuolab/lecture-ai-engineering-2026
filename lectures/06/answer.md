# 第6回 解答

## 演習

- `--list-tools` で見えたツール名と、第3回（`--mcp` なし）との違い：
    - glossary_search_glossary
    - --mcpなしの時は3個のツールが見えていた（search_glossary, get_lecture_summary, make_quiz）
- `--mcp --trace` で見えたツール呼び出し（ツール名と引数）と、`requests` の回数：
    - glossary_search_glossary({'query': '3レベル'})、`requests`は2回
- MCP サーバーに公開したツールと、その説明文：
  - `glossary_search_glossary`（引数: `query: str`）
  - 説明文：`講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について答える前に使うこと。query には調べたい用語を1つだけ入れる。`
- fetch サーバーを足したときのツール呼び出し（ツール名と引数）：`fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`と`glossary_search_glossary({'query': 'MCP'})`、`requests` は3回

## 宿題

- 取り組んだレベル：基礎
- やったこと：
  - `uv run python -m app.mcp_server --http` で、MCP サーバーを `http://127.0.0.1:8000/mcp` に起動した。
  - `app/mcp_servers.json` の `glossary` を、stdio 用のコマンド指定から HTTP の URL 指定に変更した。
  - 設定を切り替えた状態で、`uv run python -m app.agent --mcp --trace "AIE2026の講座の宿題にある「3レベル」とは何ですか？"` を実行した。
- 結果：
  - HTTP 接続でも `glossary_search_glossary({'query': '3レベル'})` が呼ばれ、回答は「基礎・実装・発展」の3レベルとして返った。
  - trace の `requests` は2回、`tool_calls` は1回だった。
  - stdio 接続でも同じツール名・引数、`requests=2`、`tool_calls=1`だった。
- 気づき・疑問：
  - stdio はクライアントがサーバーをサブプロセスとして起動する方式で、1回の接続ごとにプロセスを管理する。
  - Streamable HTTP はサーバーを別プロセスとして起動し、ポート経由でクライアントから接続する方式なので、起動と接続を分けて管理できる。
