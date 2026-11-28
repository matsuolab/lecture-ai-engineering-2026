# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：
    search_materials
    glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：
    aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'})
    aws_aws___search_documentation({'search_phrase': '"What is versioning" Amazon S3'})
- 気づき・疑問：
    演習の手順とmcp_serverに追加することでエージェントとモデルが自動的にどのように解釈しているかの概要は理解できた。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：glossary_get_lecture_summaryの追加
- 結果：
    [tool call]   glossary_get_lecture_summary({'lecture': 2})
    [tool return] glossary_get_lecture_summary -> # 第2回 ファインチューニングとLoRA
- 気づき・疑問：
    ただ実行しているだけのtest_agent.pyも理解が必要
