# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：演習では講義回数を指定するとプログラムが講義の問題を生成し回答する
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  1 search_glossary 引数: {"query": {"type": "string"}}
  2 get_lecture_summary 引数: {"lecture": {"type": "integer"}}
  3 make_quiz  引数: {"lecture": {"type": "integer"}}
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：
  追加したツール：　make_quiz
  docstringの説明：引数に講義回数をとり、search_glossaryの２回目の講習から質問をランダムに得て回答する

## 宿題

- 取り組んだレベル：基礎 
- やったこと：チャットにmake_quizのDocstringを貼り付けてmake_quiz関数を実装させた。
- 結果：Docstringの指定通り、tools.pyにmake_quiz関数を追加して、agent.pyのTODOの部分にtoolを設定して、実行も確かだった。
- 気づき・疑問：Docstringの様な曖昧な指定で実際動作するプログラムが生成できるのは不思議だ。
