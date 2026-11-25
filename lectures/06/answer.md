# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：search_materials
　　　　　　　　　　　　　glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要', 'topics': ['general']})
aws_aws___search_documentation({'search_phrase': 'Using versioning Amazon S3 bucket overview', 'topics': ['general']})
[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon Route 53 features what is', 'topics': ['general']})

- 気づき・疑問：MCPサーバーを通じて、内部のツールや公開されているサーバーや外部で動くサーバーに接続し、回答を取得できることを確認した。特に、外部動くサーバーに追加の質問を投げたところ、日本語で投げた指示をモデルが適宜英訳し、外部サーバーに投げてることが確認できた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
