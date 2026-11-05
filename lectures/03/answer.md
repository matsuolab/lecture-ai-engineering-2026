# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLMは講座固有の内容を知らず、「分からない」と答えるか一般論になる。エージェントは search_glossary で用語集を検索してから答えたため、回答が用語集の定義（基礎・実装・発展、どれか1つで完了）に沿い、最後に「第1回」が付いた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「LoRA とQLoRAの違いは？」：search_glossary({'query': 'LoRA'})、search_glossary({'query': 'QLoRA'})。docstring の「用語を1つだけ入れる」に従い、1語ずつ別々に検索された。
  - 「第2回の内容から確認問題を1問出して」：make_quiz({'lecture': 2})
- 1つの質問での LLM 呼び出し回数（`requests`）：どちらも requests=2（tool_calls は LoRA/QLoRA が 2、make_quiz が 1）。1回目でツール呼び出しを依頼し、2回目でツールの結果を見て回答した。LoRA/QLoRA は2件の検索を1回の依頼にまとめたので、tool_calls=2 でも requests は 2 だった。
- 追加したツールと、docstring に書いた説明：make_quiz(lecture: int)。指定した回の用語を用語集から1つ選び、「○○の意味は？」という問題と答え（definition）を JSON で返す。該当する用語が無い回（lecture=0 など）はエラーにせず「用語集にありません」と返す。
 - docstring：「指定した回の用語から1つを選び、確認問題と答えを返す。『第2回の確認問題を出して』のように、復習用の問題を求められたときに使う。lecture には回の番号（1始まりの整数）を入れる。」



## 宿題

- 取り組んだレベル：基礎
- やったこと：app/agent.py の INSTRUCTIONS から「必ず search_glossary で用語集を確認する」の行を消し、「3レベル」の質問を --trace 付きで実行して、消す前と比べた（モデルは gemini-3.1-flash-lite に固定）。変えたのはこの1か所だけ。
- 結果：消す前も後も、search_glossary({'query': '3レベル'}) が1回呼ばれ、requests=2、tool_calls=1 だった。回答は用語集の定義に沿い、最後に「第1回」が付いた。入力トークンは 915 → 765 に減った。
- 気づき・疑問：行を消しても動きは変わらなかった。search_glossary の docstring に「答える前に使うこと」があるため、モデルはそちらを読んで検索した可能性がある。INSTRUCTIONS と docstring の両方が同じ指示を出していると、片方を消しても動きは変わらないのではないか。docstring の一文も消すと検索しなくなるのか、確かめたい。
