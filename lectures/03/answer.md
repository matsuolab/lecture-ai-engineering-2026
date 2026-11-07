# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：素のLLMにはなかった知識を、エージェントは用語集を検索して正確に答えた
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary、make_quiz
- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：make_quizと、クイズや復習問題の呼び出し

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - `app/tools.py` に `learning_log/` フォルダへファイルを出力する `save_learning_log` ツールを追加した。
  - `app/agent.py` で `agent.tool_plain(save_learning_log, requires_approval=True)` と `output_type=[str, DeferredToolRequests]` を設定し、ファイル書き込み前に承認を求めるHuman-in-the-loop構成を実装した。
- 結果：`save_learning_log` を呼び出そうとした段階で処理が中断され、`DeferredToolRequests`（承認待ち）が発生することを確認した。

- 気づき・疑問：
   - 不可逆な処理行うツールには、`requires_approval=True` による人間の確認ステップを挟むことで、安全で制御可能なエージェントが構築できることを学んだ。
   