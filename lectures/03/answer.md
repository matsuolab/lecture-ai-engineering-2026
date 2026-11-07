# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLMでは過去の回答の参照やツールの利用ができない。
- `--trace` で見えたツール呼び出し（ツール名と引数）：[tool call]   search_glossary({'query': 'LoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：
def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """

## 宿題

- 取り組んだレベル：基礎
- やったこと：「用語集を必ず確認せよ」という指示を無くした。
- 結果：
説明が簡潔になった。出力トークンが減少(228⇒177)、コストも減少(0.0009288⇒0.0007869)
- 気づき・疑問：
「用語集を必ず確認せよ」という指示を無くしたが、LLMは確率的な挙動をすると考えると、
指示を無くさなくても用語集を確認に行かないこともあるのではないか。
この逆（「用語集を必ず確認せよ」という指示を無くた）場合は、
そもそも用語集の存在がわからないので、確率的にも用語集を見に行くことはないのではないかと
推測する。
- 実験結果
【変更前】
@masudahirokazu ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --trace "LoRA とQLoRAの違いは？"
[model] gemini-3.5-flash-lite
LoRAとQLoRAの主な違いは、**ベースモデルの重みをそのまま使うか、量子化してメモリを大幅に節約するか**という点にあります。

* **LoRA（Low-Rank Adaptation）**
  * 事前学習済みの重みは固定し、重みの更新分を低ランク行列（2つの小さな行列の積）で近似して、その部分だけを学習するPEFT（Parameter-Efficient Fine-Tuning）手法です。学習パラメータや保存ファイルを大幅に削減できます。
* **QLoRA（Quantized LoRA）**
  * ベースモデルの重みを4ビットなどに量子化（低精度化）してメモリ使用量を極限まで抑えたうえで、LoRAによるファインチューニングを行う手法です。これにより、限られたGPUメモリでもより大きなモデルを扱うことが可能になります。

関係する回：第2回

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0009288'), details={'text_prompt_tokens': 1196}, input_text_tokens=1196, input_tokens=1196, output_tokens=228, requests=2, tool_calls=2)
@masudahirokazu ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ 


【変更後】
(aie2026-exercises) @masudahirokazu ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --trace "LoRA とQLoRAの違いは？"
[model] gemini-3.5-flash-lite
LoRAとQLoRAの主な違いは、**ベースモデルの重みの扱い方**にあります。

* **LoRA**: 事前学習済みの重みはそのまま（通常は16ビットなどの精度）固定し、重みの更新分を低ランク行列で表現してその部分だけを学習する手法です。
* **QLoRA**: LoRAの仕組みをベースにしつつ、さらにベースモデルの重みを**4ビットなどに量子化（圧縮）**してメモリ消費を大幅に抑えたうえで学習する手法です。これにより、より大きなモデルを小さなGPU環境でも扱えるようになります。

関係する回：第2回

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0007869'), details={'text_prompt_tokens': 1148}, input_text_tokens=1148, input_tokens=1148, output_tokens=177, requests=2, tool_calls=2)
(aie2026-exercises) @masudahirokazu ➜ /workspaces/lecture-
