# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
今回の回答は第1回の要約と似ていますが、正解と比べると「スキルや理解度に合わせて難易度を分ける」という説明は講座固有の定義ではありません。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call] search_glossary({'query': 'LoRA'})
[tool call] search_glossary({'query': 'QLoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）： requests=2
- 追加したツールと、docstring に書いた説明：
`make_quiz(lecture: int)`
指定した回の用語から1つ選び、確認問題と答えを返す。復習問題を求められたときに使う。
- `make_quiz` の実行結果：
  第2回の用語から「量子化」が選ばれ、問題と答えが返った。trace では `make_quiz({'lecture': 2})`、`tool_calls=1`、`requests=2` を確認した。
- テスト結果：`12 passed`

## 宿題

- 取り組んだレベル：基礎
- やったこと：make_quiz のdocstringに、答えと短い解説も返すよう追記し、同じ確認問題の質問を --trace 付きで実行した。
- 結果：変更前は答えを伏せて考えるよう促したが、変更後は選ばれた用語（PEFT）の定義を答えとして表示した。ツールは make_quiz({'lecture': 2}) で、tool_calls=1、requests=2だった。
- 気づき・疑問：出題される用語はランダムなので、回答形式の変化を比較した。
