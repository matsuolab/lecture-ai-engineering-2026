# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：search_materials, glossary_search_glossary
- STEP 2 の [tool call]： glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]： fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})
aws_aws___search_documentation({'topics': ['general'], 'search_phrase': '"Using versioning" Amazon S3 versioning overview'})
- 気づき・疑問：MCPでは、サーバー名とツール名を組み合わせた名前がモデルに渡されるため、同じ名前のツールでもサーバーごとに区別できると分かった。一方で、ツールの説明文や引数の設計が不十分だと、モデルが誤った引数で呼び出したり不要なサーバーを選んだりする可能性がある。今回のAWS MCPでは検索語が一度だけとは限らず、回答に必要なキーワードを段階的に絞っていくこともできそうだが、どこまでをツール側の責務にし、どこまでをエージェント側の質問文で指定するかは疑問として残る。また、外部サーバーに接続する場合は、URLや検索語などの内容が提供者へ送られるため、社内情報を渡す前に提供元と権限、取得先の制限を確認する必要がある。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：実装
- やったこと：実装レベルを選び、`app/tools.py` に指定した回の用語から確認問題を1問作る `make_quiz` を追加した。存在しない回では例外を出さず、登録されている回を案内するメッセージを返すようにし、`app/mcp_server.py` で `glossary_make_quiz` として公開した。
- 結果：範囲内の第2回では問題と答えを返し、範囲外の第99回では「第99回の確認問題は作れません」と案内することをユニットテストで確認した。MCP経由でもツール一覧への公開と、ツール結果がクライアントに戻ることをテストで確認した。実際の `--trace` では `[tool call] glossary_make_quiz({'lecture': 99})` と呼ばれ、`[tool return]` で登録されている回の案内が返った。
- 気づき・疑問：`return` で返した範囲外メッセージは `[tool return]` としてモデルに渡されるため、例外よりも復旧可能な選択肢を含められる。ツールの説明文が曖昧だと引数の回番号が誤る可能性があるため、引数の範囲や戻り値の形式を明確にする必要がある。
