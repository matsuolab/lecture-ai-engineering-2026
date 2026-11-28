# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLMは講座の情報を参照できず、「初級・中級・上級などの3段階の可能性が高い」と一般論で推測していた。エージェントは用語集を検索したうえで、「基礎（講義内容の確認）・実装（自分でコードを書く）・発展（調査や試行）の3つで、どれか1つに取り組めば完了」と講座に固有の内容を答え、最後に関係する回（第1回）も示した。
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` の2回。docstring に「query には調べたい用語を1つだけ入れる」とあるため、2つの用語を別々に検索していた。
- 1つの質問での LLM 呼び出し回数（`requests`）：requests=2、tool_calls=2。第1回の app.ask は1回だったので、エージェントは呼び出し回数が増える
- 追加したツールと、docstring に書いた説明：make_quiz(lecture: int)`。docstring は「指定した回（1始まりの整数）の用語から1つを選び、確認問題と答えを返す。「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。」`--trace` で `make_quiz({'lecture': 2})` が呼ばれ、`pytest -q` もすべて passed した。

## 宿題

- 取り組んだレベル：実装 
- やったこと：- `app/tools.py` に、学習の記録を `learning_log/` に Markdown で保存する `save_learning_log(content: str)` を追加した（空の内容では保存しない）
- `app/agent.py` で `requires_approval=True` を付けて登録し、`output_type=[str, DeferredToolRequests]` にした
- CLI に `ask_approvals` を追加し、承認待ちのツール名と引数を表示して y/n を聞き、`DeferredToolResults`（承認は True、拒否は `ToolDenied`）を渡して `message_history` から続きを実行するようにした

- 結果：質問：「今日学んだこと「LoRAは低ランク行列だけを学習する手法」を学習記録に保存して」
- y（承認）：`[tool call] save_learning_log({'content': '今日学んだこと：LoRAは低ランク行列だけを学習する手法'})` → `learning_log/20261106-150812.md` に保存された。requests=2、tool_calls=2
- n（拒否）：ツールは実行されず、`[tool return] save_learning_log -> 利用者が保存を拒否しました。` がモデルに返り、モデルは「保存がキャンセルされました」と答えた。ファイルは作られなかった
- `uv run pytest -q`：13 passed

- 気づき・疑問：- 最初は docstring に「保存の前に利用者の確認を挟む」と書いていたため、モデルがツールを呼ばずに文章で「よろしいでしょうか？」と聞いて終わってしまった。確認はプログラム側（requires_approval）が行うので、docstring からこの行を消し、INSTRUCTIONS に「確認の文は書かずに save_learning_log を呼ぶ」と足したところ、承認待ちで止まるようになった。docstring の1文でツールを呼ぶかどうかが変わることを実感した
- 全角の「ｙ」を入力すると拒否扱いになった。`unicodedata.normalize("NFKC", ...)` で半角に変換して対応した
- 承認後の再開は新しい実行なので、`result.usage` の requests は再開後の分だけが数えられているように見えた（拒否時は requests=1）。1つの質問での合計回数を出すには、1回目の実行の usage も足す必要がありそう
- 保存ファイル名の時刻が UTC になっていた（Codespaces のサーバー時刻
