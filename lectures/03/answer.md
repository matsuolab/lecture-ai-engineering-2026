# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：エージェントは回答前に用語集を検索し、ツールの結果を使って回答する。
- `--trace` で見えたツール呼び出し（ツール名と引数）：LoRAの質問では `search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` が呼ばれた。確認問題では `make_quiz({'lecture': 2})` が呼ばれた。
- 1つの質問での LLM 呼び出し回数（`requests`）：LoRAの質問は2回、確認問題は2回だった。検索や問題生成の結果を受けてから回答するため、質問だけの場合より呼び出し回数が増える。
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture)` を追加。「指定した回の学習内容から、確認問題を1問作るときに使う」と説明し、指定回の用語を1つ選んで問題と定義を JSON で返す。

## 宿題

- 取り組んだレベル：実装
- やったこと：`save_learning_log(entry)` を追加し、`learning_log/` に日時付き Markdown として保存できるようにした。保存は `requires_approval=True` で登録し、CLI で利用者が許可した場合だけ保存して会話を再開するようにした。
- 結果：承認待ちの結果を `DeferredToolRequests` として扱い、`y` の入力後に `DeferredToolResults` を渡して再実行できた。`save_learning_log` が呼ばれ、`learning_log/` に記録が保存された。`uv run pytest -q` で 15 件すべて成功した。
- 気づき・疑問：ツールの実行結果だけでなく、承認待ちの状態もエージェントの出力として扱う必要がある。拒否した場合は保存せず、モデルに拒否結果を返せる。
