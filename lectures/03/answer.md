# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLMは「3レベル」を一般的な難易度の3段階だと推測し、具体例も含めて回答した。エージェントは用語集を検索し、「基礎・実装・発展のどれか1つに取り組めば完了」と講座固有の定義を回答した。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
	--- trace ---
	[tool call]   search_glossary({'query': 'LoRA'})
	[tool call]   search_glossary({'query': 'QLoRA'})
	[tool return] search_glossary -> [{"term": "LoRA", ...}]
	[tool return] search_glossary -> [{"term": "QLoRA", ...}]
	[usage] RunUsage(... requests=2, tool_calls=2)
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture: int)`。指定した回の用語から1つ選んで確認問題と答えを返す。「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。

## 宿題

- 取り組んだレベル：基礎
- やったこと：①②の変更をそれぞれ個別に適用し、各条件で「LoRAとQLoRAの違いは？」と質問した。① INSTRUCTIONSから「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。」を削除した。② docstringを「用語を1つだけ入れる」から「用語をまとめて入れる」に変えた。
- 結果：
	① の場合：
	```text
	--- trace ---
	[tool call]   search_glossary({'query': 'LoRA'})
	[tool call]   search_glossary({'query': 'QLoRA'})
	[tool return] search_glossary -> [{"term": "LoRA", ...}]
	[tool return] search_glossary -> [{"term": "QLoRA", ...}]
	[usage] RunUsage(... requests=2, tool_calls=2)
	```
	最終回答ではLoRAとQLoRAの違いを説明し、末尾に「第2回」と示した。変更前と比べて内容面で大きな差はなかった。
	② の場合：
	```text
	--- trace ---
	[tool call]   search_glossary({'query': 'LoRA QLoRA'})
	[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
	[usage] RunUsage(... requests=2, tool_calls=1)
	```
	②の検索結果にはLoRAとQLoRAの両方が含まれた。モデルの最終回答でも両方の用語を説明した。最終回答では「Low-Rank Adaptation」「Quantized LoRA」の名称を挙げ、それぞれの定義と特徴を詳しく説明し、「関係する回：第2回」と示した。用語集に沿った内容で、主な違いは説明の詳しさと書式だった。
- 気づき・疑問：①の場合、ツールのdocstringが検索を促すことがある。②の場合、用語をまとめて検索するとツール呼び出しは2回から1回に減ったが、LLM requestsは2回のままだった。複数の用語を1つのqueryにまとめた場合、曖昧さや検索結果数の上限（MAX_RESULTS）によって、必要な用語を取りこぼすことはないかが気になった。
