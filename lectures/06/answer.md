# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]： fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'}),aws_aws___search_documentation({'topics': ['general'], 'search_phrase': '"Versioning" "bucket" site:docs.aws.amazon.com/AmazonS3/latest/developerguide'})

- 気づき・疑問：STEP４ではAWSでツールが二回呼ばれている可能性がある。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：server.tool()(tools.get_lecture_summary)をapp/answer.mdに追加した。
- 結果：[glossary_get_lecture_summary]
  指定した回（1始まりの整数）の講義の要点を返す。
  
  「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
  引数: {"lecture": {"title": "Lecture", "type": "integer"}}[tools] MCP サーバー（app/mcp_servers.json）
第2回では、**「ファインチューニングとLoRA」**をテーマに学びます。

主な内容は以下の通りです：

1. **事前学習とファインチューニングの違い**
   - 事前学習で汎用的な言語能力を身につけたモデルを、特定の目的に合わせて追加学習させる方法や、向く場面・向かない場面について理解します。
2. **SFT（教師あり微調整）**
   - 入力と望ましい出力のペアを用いて、データの質や形式が結果に与える影響を確認します。
3. **PEFTとLoRA（Low-Rank Adaptation）**
   - 全パラメータを更新するのではなく、小さな低ランク行列だけを追加して学習することで、メモリや計算コストを大幅に削減する仕組み（および主なハイパーパラメータやQLoRAとの違い）を学びます。
4. **演習**
   - Google Colab上で小さなモデルをLoRAで学習させ、学習の前後でモデルの出力形式や回答の精度がどう変化するかを体験します。

関連する回：第2回

--- trace ---
[tool call]   glossary_get_lecture_summary({'lecture': 2})
[tool return] glossary_get_lecture_summary -> # 第2回 ファインチューニングとLoRA

## この回のねらい

- 事前学習とファインチューニングの違い、ファインチューニングが向く場面と向かない場面を理解する
- LoRAの考え方を理解し、Google Colab上で小さなモデルを…
[usage] 入力 5,942 tokens / 出力 254 tokens / モデル応答 2 回
以上のような内容が出力された。


- 気づき・疑問：最後に途切れているのが仕様なのかが気になった。モデル応答2回というのが、どのタイミングで呼ばれたかが気になった。
