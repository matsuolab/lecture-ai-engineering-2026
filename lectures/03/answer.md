# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：LLMは学習済みの知識から回答する。エージェントは用語集を検索し、その結果を参照して回答する。
- `--trace` で見えたツール呼び出し（ツール名と引数）：--traceで確認した結果、LoRAとQLoRAの違いを質問した際、search_glossaryが次の引数で呼び出された。{"query":"LoRA"}{"query":"QLoRA"}
- 1つの質問での LLM 呼び出し回数（`requests`）：LoRAとQLoRAの比較では、requests=2,tool_calls=2
- 追加したツールと、docstring に書いた説明：make_quiz(lecture:int)を追加。
docstring には、確認問題を求められたときに使用することを記載

## 宿題

- 取り組んだレベル：基礎 
- やったこと：agent.pyのINSTRUCTIONSに、複数の用語を比較するときは個別に検索する指示を追加。tools.pyのsearch_glossaryのdocstringにも、用語ごとにツールを１回ずつ呼び出す説明を追加。同じ質問「LoRAとQLoRAの違いは？」をtraceつきで実行。
- 結果：INSTRUCTIONS変更後は、search_glossaryがLoRAとQLoRAについて各１回、合計２回呼び出され、両者の違いが回答された
- 気づき・疑問：指示追加でAIのツール利用を制御できることがわかった。５０３エラーが頻発しているのでいったんこれで提出まで行う。
- 取り組んだレベル：実装 
- やったこと：学習記録を保存するsave_learning_logツールを追加。保存前に利用者の承認を求めるようにした
- 結果：保存前に承認確認が表示された。
- 気づき・疑問：コードが理解できていない