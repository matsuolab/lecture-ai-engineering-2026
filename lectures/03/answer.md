## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  素のLLM（app.ask）は講座固有の知識がなく、「3レベル」の質問に対して一般論で回答した。
  エージェント（app.agent）は答える前に search_glossary で用語集を検索し、
  基礎・実装・発展の正確な定義を返した。また回答末尾に「関係する回：第N回」が付いた。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
  [tool call] search_glossary({'query': 'LoRA'})
  [tool call] search_glossary({'query': 'QLoRA'})
  LoRA と QLoRA がそれぞれ別のクエリで検索された。
  docstring に「query には用語を1つだけ入れる」と書かれているためモデルがその通りに動いた。

- 1つの質問での LLM 呼び出し回数（`requests`）：
  requests=2（ツール呼び出し前の1回＋ツール結果を受け取って回答する1回）

- 追加したツールと、docstring に書いた説明：
  make_quiz(lecture: int) -> str を app/tools.py に追加し、app/agent.py で登録した。
  docstring：「指定した回の用語から1つを選び、確認問題と答えを返す。
  『第2回の確認問題を出して』のように、確認問題や復習を求められたときに使う。
  lecture には回の番号（整数）を渡す（例: 2）。」

## 宿題

- 取り組んだレベル：基礎

- やったこと：
  INSTRUCTIONS から「必ず search_glossary で用語集を確認する」の行を削除し、
  さらに docstring から「答える前に使うこと。」の行も削除して、
  同じ質問（「LoRAとQLoRAの違いは？」）を --trace 付きで実行して比較した。
  また「2+2はいくつですか？」でツールが呼ばれない場合も確認した。

- 結果：
  【変更前】requests=2、tool_calls=2（search_glossary が2回呼ばれた）
  【INSTRUCTIONS の行を削除後】requests=2、tool_calls=2（変化なし）
  【docstring の「答える前に使うこと」も削除後】requests=2、tool_calls=2（それでも変化なし）
  【「2+2はいくつですか？」】requests=1、tool_call なし

- 気づき・疑問：
  INSTRUCTIONSとdocstringの両方から検索を促す指示を削除しても、
  LoRAのような技術用語の質問ではモデルが自分の判断でツールを使い続けた。
  モデルは指示ではなく文脈からツールの必要性を推論しており、
  「2+2」のような一般的な質問では指示がなくてもツールを呼ばなかった（requests=1）。
  
  そのため、特定の場面でツールを使わせたくない場合、「使わないこと」と指示するよりも
  そもそもツールを登録しない（モデルに選択肢を与えない）方が確実だとわかった。
  INSTRUCTIONSやdocstringの指示は、モデルの判断を強制するのではなく
  誘導・補助する役割に近い。
