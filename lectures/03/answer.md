# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
素のLLMは用語集を参照せずに答えるため、AIE2026固有の「宿題の3レベル」を正確に説明できないことがある。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
`LoRAとQLoRAの違いは？`という質問では、`search_glossary`が呼ばれる。例：`[tool call] search_glossary({'query': 'LoRA'})`、`[tool call] search_glossary({'query': 'QLoRA'})`。実際の引数や呼び出し回数はモデルの実行結果に合わせて記録する。

- 1つの質問での LLM 呼び出し回数（`requests`）：
`--trace`末尾の`[usage]`に表示される`requests`の値を記録　2回
ツール呼び出しを決めるリクエストと、ツール結果を受けて回答するリクエストで2回。モデルが追加のツール呼び出しを行う場合は増える。

- 追加したツールと、docstring に書いた説明：
`make_quiz(lecture: int)`を追加し、「指定した回の用語から1つ選び、用語の意味を問う確認問題と答えを返す」「講義内容の復習問題を求められたときに使う」と説明した。指定回の用語をランダムに選び、`{"question": "「用語」の意味は？", "answer": "用語のdefinition"}`の形式で返す。

## 宿題

- 取り組んだレベル：基礎

- やったこと：
`app/agent.py`の`INSTRUCTIONS`を1箇所だけ変更し、「質問に複数の用語が含まれる場合は、用語ごとに個別に検索する」と追加した。変更前後で同じ質問「LoRAとQLoRAの違いは？」を`--trace`付きで実行した。

- 結果：
変更前は`search_glossary({'query': 'LoRA'})`の1回だけで、`requests=2`、`tool_calls=1`だった。
変更後は`search_glossary({'query': 'LoRA'})`と`search_glossary({'query': 'QLoRA'})`の2回が呼ばれ、`requests=2`、`tool_calls=2`だった。変更後の回答では、両方の用語について用語集の定義を参照していた。

- 気づき・疑問：
指示を変えると、最終回答までのLLMリクエスト数は同じでも、ツールの呼び出し方と用語集から得る結果が変わった。複数のツール呼び出しを1回のLLM応答でまとめて要求できるため、`requests`と`tool_calls`は別の数になる。
