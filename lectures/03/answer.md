# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
第1回では、モデルは正確ではないとは言いつつも、モデルが独自に考えた一般論としての3レベルをいくつか挙げていた。
一方、第3回ではglossary.jsonの内容をそのまま答えており、一般論ではなく、今回の講座に沿った正しい回答となっていた。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA",...
[tool return] search_glossary -> [{"term": "QLoRA",...
[usage] RunUsage(cost=Decimal('0.0008163'),...
[model] gemini-3.5-flash-lite

- 1つの質問での LLM 呼び出し回数（`requests`）：
requests=2

- 追加したツールと、docstring に書いた説明：
make_quizというツールを追加した。intを入力してstrを返す。
docstringは、    
    """
    指定した回の用語から一つを選び、確認問題と答えを返す。
    「第２回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """


## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
基礎

- やったこと：
1. app.agent.pyのINSTRUCTIONSを変更した
修正前
INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
"""
修正後
INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。
- 回の内容を聞かれたら get_lecture_summary を使う。
- 用語や講座に固有のことを聞かれたら、search_glossary で用語集を確認する。
- 用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。
- 回答の最後に、関係する回（第N回）を示す。
- 宿題の答えそのものは書かず、考え方のヒントで導く。
"""

2. app.tools.pyのsearch_glossaryのDocstringを修正した。
修正前
   """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を一つだけ入れる（例: "LoRA"）。
    """

修正後
   """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を複数入れる（例: "LoRA"）。
    """

- 結果：
1. 
uv run python -m app.agent --trace "LoraとALoraの違いは？"

修正前
LoRAとQLoRAの違いは以下の通りです。
* **LoRA**: 事前学習済みの重みを固定したまま、重みの更新分を2つの小さな行列（低ランク行列）で表し、その小さな行列だけを学習するPEFT（Parameter-Efficient Fine-Tuning）手法です。学習パラメータや保存ファイルを大幅に削減できます。
* **QLoRA**: ベースモデルの重みを4ビットなどに量子化してメモリ消費を大幅に節約した状態で、LoRAによる学習を行う手法です。LoRAの利点を活かしつつ、より大きなモデルを比較的小さなGPUで扱えるようにします。
関係する回：第2回
--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…

修正後
**LoRA**と**QLoRA**の主な違いは、**ベースモデルの重みを量子化（ビット数を減らす）するかどうか**にあります。
* **LoRA（Low-Rank Adaptation）**
  事前学習済みの重みは固定したまま、重みの更新分を小さな低ランク行列（学習パラメータ）のみで近似し、その部分だけを効率よく学習する手法です。
* **QLoRA（Quantized LoRA）**
  LoRAの仕組みに加え、ベースモデルの重みを4ビットなどに量子化（低精度化）することでメモリ消費を大幅に抑え、より大きなモデルを小さなGPU環境でも学習できるように拡張した手法です。
関連する回：第2回
--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…

2.
修正後
**LoRA**と**QLoRA**の主な違いは、ベースモデルの重みをそのまま使うか、量子化してメモリを節約するかにあります。
* **LoRA（Low-Rank Adaptation）**
  * **仕組み**: 事前学習済みの重みを固定したまま、重みの更新分を低ランク行列（2つの小さな行列の積）で近似し、その小さな行列だけを学習する手法です。
  * **特徴**: 学習パラメータを大幅に削減でき、アダプタと呼ばれる小さなファイルで効率的にファインチューニングを行えます。第2回の演習では、このLoRAを実際に扱います。
* **QLoRA（Quantized LoRA）**
  * **仕組み**: ベースモデルの重みを4ビットなどに**量子化**（精度を落としてデータ量を圧縮）してメモリ消費量を大幅に節約した上で、LoRAの仕組みを使って学習を行う手法です。
  * **特徴**: より巨大なモデルであっても、VRAM容量の小さいGPUで効率よく扱えるようになります。
このように、LoRAが「低ランク行列による効率的な学習」に焦点を当てているのに対し、QLoRAはそれに加えて「ベースモデルの量子化によるさらなる省メモリ化」を実現している点が大きな違いです。
（関連する回：第2回）
--- trace ---
[tool call]   search_glossary({'query': 'LoRA QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…

- 気づき・疑問：
1のINSTRCTIONを変更した場合では、文章の順番を入れ替えたり、必ずという文言をやわらげたりしたが、出力に大きな違いはなかった。
2のDocstringのqueryへ入力する用語を複数okにした場合では、一度にLoraとQLoRAがqueryに入力されており、LoRAとQRoLAを比較した文章が修正後には追加されていた。
make_quizでJSON形式で返すように指定したが、返り値はjson形式になったが、最終回答はJSON形式になっていなかった。