# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 【Codespacesで `uv run python -m app.agent "AIE2026の講座で使う「lecNN-start タグ」とは何ですか？"` を実行し、第1回の `app.ask` の回答と比べて記入】
  - 観点：素のLLMは講座固有の用語を知らないため一般論や推測で答えるのに対し、エージェントは `search_glossary` で用語集を引いてから答えるので、定義と「第N回」が正しく入るかを確認します。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 【`uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"` の `[tool call]` 行を貼る】
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - 【上の `[usage]` の `requests` を記入】
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int)`：指定した回の用語から1つを選び、「〇〇の意味は？」という問題と、用語集の定義を答えとして JSON で返します。
  - docstring には「確認問題を求められたときに使う」ことと、「answer は利用者が答えたあとに示す」ことを書きました。INSTRUCTIONS にも「答えは問題と一緒に見せない」を1行足しています。
  - 【`uv run python -m app.agent --trace "第2回の内容から確認問題を1問出して"` の結果を貼る】

## 宿題

- 取り組んだレベル：実装

- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を作りました。`learning_log/YYYY-MM-DD.md` に、その日の記録を `## HH:MM 見出し` の形で追記します（上書きではなく追記にして、過去の記録を消さないようにしました）。`learning_log/` は `.gitignore` 済みです。
  - `app/agent.py` で `requires_approval=True` を付けて登録し、エージェントの `output_type` を `[str, DeferredToolRequests]` にしました。
  - CLI に `run_with_approval()` を追加しました。実行が `DeferredToolRequests` で止まったら、ツール名と引数（title / content）を表示して `[y/N]` で確認し、承認なら `True`、拒否なら `ToolDenied("利用者が保存を許可しませんでした…")` を `DeferredToolResults` に入れて、`message_history` と一緒に続きを実行します。承認待ちが続く限りこれを繰り返します。
  - 承認の前後で LLM を2回に分けて呼ぶため、2回目に `usage=result.usage` を渡し、`[usage]` が合算されるようにしました。
  - TestModel を使ったテスト `tests/test_approval.py` を追加しました（LLM・APIキー不要）。
    - 承認前は `DeferredToolRequests` で止まり、ファイルは書かれない
    - 承認すると保存され、回答（str）が返る
    - 拒否すると保存されず、拒否のメッセージがモデルに戻って回答が続く
    - `run_with_approval` は利用者に1回だけ確認する
  - 既存の `test_base_tools_are_registered_and_called` は TestModel が全ツールを呼ぶため、承認待ちのツールで止まって失敗するようになりました。承認待ちのツールを除いて呼ぶように直しています。

- 結果：
  - `uv run pytest -q` → 19 passed
  - 【Codespacesで次を実行し、承認した場合と拒否した場合の出力を貼る】
    ```bash
    uv run python -m app.agent --trace "LoRAについて学んだことを学習記録に保存して。内容は「重みの差分を低ランク行列で学習するので、学習するパラメータが少ない」"
    cat learning_log/*.md
    ```
  - 【承認時】`[承認待ち] save_learning_log` の表示 → `y` → `[tool return] save_learning_log -> 保存しました: learning_log/…` / `requests` の回数：
  - 【拒否時】`n` → `[tool return] save_learning_log -> 利用者が保存を許可しませんでした…` / ファイルが増えていないこと / モデルの回答：

- 気づき・疑問：
  - 承認を挟むと、エージェントの実行は「止まって、外から結果を渡して再開する」2回の `run_sync` に分かれます。会話履歴（`message_history`）を渡し直すことで続きから再開できる、という作りが、第1回の `--chat` で履歴を自分で持っていたのと同じ考え方だと分かりました。
  - TestModel は登録されたツールを全部呼ぶので、承認付きのツールを足すと既存のテストが止まります。ツールを足すたびに「どのテストがどのツールを呼ぶか」を意識する必要がありました。
  - 【実行してみて気づいたことを追記：例）モデルが「保存して」と言われる前に自分から save_learning_log を呼ぶことがあるか、title / content をどう要約したか】
  - 疑問：`--mcp` で MCP サーバー経由のツールを使う場合、承認が必要かどうかはサーバー側とクライアント側のどちらで決めるのがよいのか（第5回で確かめたいです）。
