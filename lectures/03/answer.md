# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：LLMは学習済みの知識から回答する。エージェントは用語集を検索し、その結果を参照して回答する。
- `--trace` で見えたツール呼び出し（ツール名と引数）：--traceで確認した結果、LoRAとQLoRAの違いを質問した際、search_glossaryが次の引数で呼び出された。{"query":"LoRA"}{"query":"QLoRA"}
- 1つの質問での LLM 呼び出し回数（`requests`）：LoRAとQLoRAの比較では、requests=2,tool_calls=2
- 追加したツールと、docstring に書いた説明：make_quiz(lecture:int)を追加。
docstring には、確認問題を求められたときに使用することを記載

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
