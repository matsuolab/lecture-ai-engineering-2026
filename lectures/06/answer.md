# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：
- STEP 2 の [tool call]：
- STEP 3 の [tool call]：
- STEP 4 の [tool call]：
- 気づき・疑問：

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：
  `app/mcp_server.py` の `TODO(宿題・基礎)` の行の下に
  `server.tool()(tools.get_lecture_summary)` の1行を追加した。
  エージェント側（`app/mcp_servers.json` / `app/mcp_agent.py`）は変更していない。
  `git status` で変更ファイルが `app/mcp_server.py` のみであることを確認した。
- 結果：
  - `uv run python -m app.mcp_agent --list-tools` が「モデルに見えているツール: 2 個」となり、
    `glossary_get_lecture_summary`（引数 `{"lecture": {"title": "Lecture", "type": "integer"}}`）
    が一覧に追加された。
  - `uv run python -m app.mcp_agent --trace "第2回では何を学びますか？"` で
    `[tool call] glossary_get_lecture_summary({'lecture': 2})` が表示され、
    第2回「ファインチューニングとLoRA」の要点が返ってきた（モデル応答 2 回）。
  - `uv run pytest -q` は 21 passed（4.42s）。
- 気づき・疑問：
  サーバー側に1行足しただけで、エージェント側を変更せずにツールが増えた。
  エージェントが起動のたびにサーバーへツール一覧を問い合わせ、その一覧をモデルに渡しているためだと分かった。
  ツール名に `glossary_` が付くのは設定ファイルのサーバー名が前につくからで、
  同じ名前のツールが複数サーバーにあっても区別できる。
  また「第2回では何を学びますか？」という質問から、モデルが `lecture=2` と引数を自分で決めていた。
  疑問：ツールの説明文（docstring）を書き換えると、選ばれ方や引数の決め方が変わるのか試してみたい。
