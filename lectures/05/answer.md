# 第5回 解答

## 演習

- `--list-tools` で見えたツール名と、第3回（`--mcp` なし）との違い：MCP経由では glossary_search_glossary のようにサーバー名が付く
- `--mcp --trace` で見えたツール呼び出し（ツール名と引数）と、`requests` の回数： glossary_search_glossary({'query': '3レベル'})、requests=2
- MCP サーバーに公開したツールと、その説明文： search_glossary（講座の用語検索）
- fetch サーバーを足したときのツール呼び出し（ツール名と引数）：fetch_fetch({'url': 'https://modelcontextprotocol.io/'}) でページを取得できた

## 宿題

- 取り組んだレベル：基礎
- やったこと：stdioとHTTP方式の比較、docstringの変更
- 結果： 両方式で正常動作した。HTTP方式ではポート8000を使用。docstring変更後もツール呼び出しは1回だった。
- 気づき・疑問：通信方式とツールの機能は独立しており、docstringの変更にはサーバーの再起動が必要だと分かった。
