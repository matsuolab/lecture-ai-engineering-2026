# 第3回 解答

> `adk web` のブラウザ画面は未確認です。ADK 版の動作は `adk run` で確認しました。

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：`lecNN-start タグ`について、`app.ask` は一般論で推測し存在しない `lecNN-end` まで説明した。エージェントは用語集を引き「各回の演習開始時点のコードに付けたGitタグ」と正しく答えた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})`。確認問題では `make_quiz({'lecture': 2})`。
- 1つの質問での LLM 呼び出し回数（`requests`）：3つの質問すべて 2 回（ツール要求で1回、結果を受けた回答で1回）。LoRA の質問は1回の応答で2ツールを並列に呼んだ。
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture: int)`。「指定した回の用語から確認問題を1問作り、問題と答えを返す。学習の確認やクイズを求められたときに使う」と記載。`uv run pytest -q` は 16 passed。

## 宿題

- 取り組んだレベル：発展 (a)（`adk web` の画面確認のみ未実施）
- やったこと：`lectures/03/advanced/aie_adk_agent/agent.py` に、同じ INSTRUCTIONS と3つのツールを使う ADK 版を作成。`google-adk` 2.14.0 は `uv.lock` を変えないよう `--with` で一時的に追加した。
- 結果：`adk run` で「LoRAとQLoRAの違いは？」に回答し、Pydantic AI 版と同じ内容で「第2回」も示した。`adk web` での見え方は未確認。
- 書き方の比較（コードから読み取れる範囲）：
  - Pydantic AI はモデルを実行時に渡すので、テストで TestModel に差し替えやすい。
  - ADK は `root_agent` の定義時にモデル名を文字列で持ち、ツールは関数のリストで渡す。実行は `adk web` などのランナー側が担う。
- 気づき・疑問：どちらも docstring と型ヒントがモデルへのツール説明になるので、`tools.py` はそのまま再利用できた。`adk web` のトレース表示と自作の `--trace` の比較は今後の課題。
