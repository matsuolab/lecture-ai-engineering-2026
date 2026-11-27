# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': '[https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 versioning overview'})
- 気づき・疑問：ほか人が作った MCP サーバーを、設定ファイルに書き足すだけで使えた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：`app/mcp_server.py` の TODO の下に `server.tool()(tools.get_lecture_summary)` を 1 行書き足し、エージェント側のコードや設定を変更せずに `--list-tools` と `--trace` による質問実行、および `uv run pytest -q` によるテストを実行した。
- 結果：`--list-tools` の一覧に `glossary_get_lecture_summary` が追加され、「第2回では何を学びますか？」の質問に対して `[tool call] glossary_get_lecture_summary({'lecture': 2})` が呼び出されて第2回の講義概要が正しく回答された。テスト（`pytest`）もすべて通過した。
- 気づき・疑問：エージェントは起動のたびに MCP サーバーへ公開ツールの一覧を問い合わせる仕組みになっているため、サーバー側でツールを追加して公開するだけで、エージェント側の実装や設定を一切書き換えずに新しいツールを認識・利用できることが分かった。
