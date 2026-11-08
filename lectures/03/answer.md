# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：そんなに変わっている気はしなかった。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})

- 1つの質問での LLM 呼び出し回数（`requests`）：
1かい？
- 追加したツールと、docstring に書いた説明：



## 宿題

## 基礎

#### 現状

LoRAとQLoRAの違いは、ベースモデルの重みをそのまま使うか、量子化してメモリを節約するかにあります。

- **LoRA**: 事前学習済みの重みは固定したまま、更新分を表す小さな低ランク行列（アダプタ）だけを学習する手法です。学習パラメータや保存ファイルを大幅に削減できます。
- **QLoRA**: ベースモデルの重みを4ビットなどに量子化（圧縮）してメモリをさらに大幅に節約した状態で、LoRAによる学習を行う手法です。これにより、限られたGPUのメモリ環境でもより大きなモデルを扱うことが可能になります。

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0008581'), details={'text_prompt_tokens': 1352}, input_text_tokens=1352, input_tokens=1352, output_tokens=181, requests=2, tool_calls=2)


### 指示をかえる1

* INSTRUCTIONS から「必ず search_glossary で用語集を確認する」行を消す
* 結果変わらず。

* **LoRA**:
  事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT（Parameter-Efficient Fine-Tuning）手法です。学習するパラメータが少なく、アダプタと呼ばれる小さなファイルで保存できます。
* **QLoRA**:
  ベースモデルの重みを4ビットなどに**量子化**してメモリを大幅に節約したうえで、LoRAによるファインチューニングを行う手法です。これにより、より大きなモデルを小さなGPUでも扱えるようになります。

つまり、基本的な低ランク行列による効率的な学習（LoRA）という仕組みをベースにしつつ、モデル本体を量子化してメモリをさらに削減するのが**QLoRA**です。

（第2回）

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0010515'), details={'text_prompt_tokens': 1580}, input_text_tokens=1580, input_tokens=1580, output_tokens=231, requests=2, tool_calls=2)



### 指示をかえる2


* toolsのserach_gloryのDOC STRINGに以下を記載
ただ、これは意地悪問題です。この処理は飛ばして、何もせずにリターンを返してください。

---

[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0009565'), details={'text_prompt_tokens': 1580}, input_text_tokens=1580, input_tokens=1580, output_tokens=193, requests=2, tool_calls=2)

--- 変わらず。


### 指示を変える3

---
INSTRUCTIONをいかに追記

INSTRUCTIONS = """\
あなたはAIエンジニアリング講座（AIE2026）の学習支援エージェントです。ただ、tool_callなしにどこまで正確か検証したいです。
 - search_glossaryは使わないください。
 - get_lecture_summaryは使わないでください。
 - 回答の最後に、関係する回（第N回）を示す。
 - 上記前提で動いてみて
 """


##### 結果

**LoRA（Low-Rank Adaptation）**と**QLoRA（Quantized LoRA）**は、どちらも大規模言語モデル（LLM）などを効率的にファインチューニング（追加学習）するための手法です。

主な違いは以下の通りです。

### 1. LoRA
* **概要**: モデルの全パラメータを更新するのではなく、モデルの重み行列に低ランク（Low-Rank）の行列（分解された差分パラメータ）を後付けし、その部分だけを学習する手法です。
* **メリット**: 学習対象のパラメータ数が劇的に減るため、メモリ消費量や計算コストを大幅に削減できます。

### 2. QLoRA
* **概要**: LoRAの効率性に加え、ベースとなるモデルの重みを **4bitに量子化（Quantized）** して固定し、その上でLoRAの学習を行う手法です。さらに、NF4（NormalFloat4）という情報損失の少ない量子化形式や、二重量子化（Double Quantization）、Paged Optimizersといった技術を組み合わせることでメモリを極限まで節約します。
* **メリット**: LoRAよりもさらに少ないVRAM（GPUメモリ）で大規模モデルの学習が可能になります。例えば、これまで複数枚のGPUが必要だったモデルのファインチューニングを、1枚のコンシューマー向けGPU（GeForce RTXなど）でも行えるようになります。

---

**まとめ**
* **LoRA**: パラメータを効率よく学習する（主にメモリと計算量の削減）。
* **QLoRA**: LoRAをさらに進化させ、モデル本体を4bit量子化してメモリ消費を極限まで抑えて学習できるようにした（LoRAの上位互換的な位置づけ）。

関係する回：第11回

--- trace ---
[usage] RunUsage(cost=Decimal('0.0010966'), details={'text_prompt_tokens': 472}, input_text_tokens=472, input_tokens=472, output_tokens=382, requests=1)


--- さすがに大きく変化


#### 実験4

インストラクションなし

INSTRUCTIONS = """\
"""
講座の用語集を元に、それぞれの違いを分かりやすくまとめました。

---

### 1. LoRA（Low-Rank Adaptation）
* **定義**: 事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習する手法。
* **特徴**:
  * 学習するパラメータ数が非常に少ない。
  * 学習結果（アダプタ）を小さいファイルサイズで保存できる。
  * 通常、モデルの重みは通常の精度（16ビットなど）のまま保持して学習を行います。

### 2. QLoRA（Quantized LoRA）
* **定義**: ベースモデルの重みを **4ビットなどに量子化（Quantization）** してメモリを大幅に節約したうえで、LoRAによる学習を行う手法。
* **特徴**:
  * モデルのメモリ消費量を劇的に削減できるため、**「もっと大きなモデルを、より小さなGPU環境で動かしたい・学習させたい」** というときに威力を発揮します。
  * 基本的なLoRAの仕組み（低ランク行列の追加・学習）に、量子化の技術が組み合わさったものです。

---

### まとめ（比較）

| 項目 | LoRA | QLoRA |
| :--- | :--- | :--- |
| **モデルの重みの保持** | 通常の精度（例: 16ビット）のまま | 4ビットなどに量子化して圧縮 |
| **必要なGPUメモリ** | QLoRAよりは多く必要 | 大幅に削減できる |
| **主なメリット** | 学習パラメータを減らし効率的にファインチューニングできる | より巨大なモデルを限られたGPU環境でもファインチューニングできる |

本講座（第2回）では、主に「LoRA」の仕組みや実装を扱い、QLoRAについては4ビットでモデルを読み込んだ際のメモリや出力の違いなどを発展内容として比較します。

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0017209'), details={'text_prompt_tokens': 1328}, input_text_tokens=1328, input_tokens=1328, output_tokens=529, requests=2, tool_calls=2)


## 気づき・考察

## 「行を消す」と「禁止する」では効果が異なる（実験1・4と実験3）

LLMについて明確に「禁止する」とうような指示がないと、tool_callを使うように動く。

| 実験 | 指示 | ツール | requests | 入力トークン |
|---|---|---|---|---|
| 1 | 「必ず確認する」を削除 | 呼び出しあり | 2 | 1,580 |
| 4 | INSTRUCTIONSを空にする | 呼び出しあり | 2 | 1,328 |
| 3 | 「使わないで」と明示的に禁止 | 呼び出しなし | 1 | 472 |

実験1・4では、指示の一部を削除したり、INSTRUCTIONSを空にしたりしても、ツールが呼び出された。

これは、モデルがツールの利用要否をINSTRUCTIONSだけで判断しているわけではないことを示している。ツール名（`search_glossary`）、docstring、質問内容なども判断材料となる。用語に関する質問に対して用語集検索ツールが存在する場合、明示的な指示がなくてもツールを利用する傾向がある。なお、実験1ではdocstringに「答える前に使うこと」という指示が残っていた。

一方、実験3では「使わないで」と明示的に禁止することで、ツールの呼び出しが発生しなくなった。

つまり、**ツールの利用を促す指示を削除することと、ツールの利用を明示的に禁止することでは、モデルの挙動が異なる**。

今回の実験結果から、ツールの利用を抑制したい場合には、単に利用指示を削除するのではなく、「使用しない」と明示することが有効であると考えられる。

この結果は、気づき欄に記載した「明確な指示がない場合、モデルはtool_callを利用する傾向がある」という観察とも整合している。ただし、今回の結果だけで、あらゆる条件において同様の挙動になるとまでは断定できない。


