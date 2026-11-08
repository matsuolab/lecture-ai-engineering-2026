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

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
