# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：[search_materials]
- STEP 2 の [tool call]：[tool call]   glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：[tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 versioning overview'})
- 気づき・疑問：MCPは外部のみではなく、別の人の作成したものをローカルでも使えるが、信頼できるかの確認が必要だが、本当に信頼できるかの判断がどうすれば100%安心して使えるかが悩ましい。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎 
- やったこと：get_lecture_summaryというツールを追加
- 結果：モデルに見えてるツールが7->8個に追加され、追加したツールが呼ばれた。
- 気づき・疑問：実装は簡単というのは理解できたが、MCPが下火になってきている理由がまだわからない。BoxやBitbucketなどでも連携しての活用ができそうな気がした。
