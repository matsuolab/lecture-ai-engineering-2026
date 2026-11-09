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

## 宿題

- 取り組んだレベル：実装

- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を作った。`learning_log/YYYY-MM-DD.md` に、その日の記録を `## HH:MM 見出し` の形で追記（過去の記録を消さないよう、上書きではなく追記にしました）。`learning_log/` は `.gitignore` 済み。
  - `app/agent.py` で `requires_approval=True` を付けて登録し、エージェントの `output_type` を `[str, DeferredToolRequests]` に。
  - CLI に `run_with_approval()` を追加。実行が `DeferredToolRequests` で止まったら、ツール名と引数を表示して `[y/N]` で確認し、承認なら `True`、拒否なら `ToolDenied("利用者が保存を許可しませんでした…")` を `DeferredToolResults` に入れて、`message_history` と一緒に続きを実行。2回目の実行には `usage=result.usage` を渡し、`[usage]` が承認前後の合計になるように設計。
  - TestModel を使ったテスト `tests/test_approval.py` を追加（承認前は止まってファイルが書かれない／承認すると保存される／拒否すると保存されず回答が続く／確認は1回だけ）。既存の `test_base_tools_are_registered_and_called` は、TestModel が全ツールを呼ぶと承認待ちで止まってしまうため、承認待ちのツールを除いて呼ぶように修正。

- 結果：
  - `uv run pytest -q` → 19 passed
  - **最初の実行（修正前）：ツールが呼ばれず。** docstring に「実行の前に利用者の承認を求める」と書いていたため、モデルが `save_learning_log` を呼ばずに「この内容で保存してもよろしいでしょうか？」と文章で聞き返して終わりました。trace は `search_glossary({'query': 'LoRA'})` の1回だけで、ファイルも作られず、CLI上保存もされず。
  - **修正：** INSTRUCTIONS に「保存前の確認はプログラムが行う。確認を求めずに呼ぶ。」を1行足した（docstring はそのまま）。
  - **承認した場合（y）：** `[承認待ち] save_learning_log`（title: LoRA / content: 重みの差分を…）が表示され、`y` で `[tool return] save_learning_log -> 保存しました: learning_log/2026-11-09.md` となった。ファイルには `## 02:49 LoRA` と内容が保存された。requests=2（承認前に1回、承認後に1回）。
  - **拒否した場合（n）：** `[tool return] save_learning_log -> 利用者が保存を許可しませんでした。…` がモデルに戻り、「学習記録の保存はキャンセルされましたが…」と回答を続けた。`cat` の結果は承認時の1件のままで、ファイルは増えていない。requests=2 で、tool_calls は数えられず（未実行）。

- 気づき・疑問：
  - 「承認を求める」と docstring に書くと、モデルは自分で確認しようとしてツールを呼ばなくなった。承認の仕組みはプログラム側にあることを、指示で明確に伝える必要があり、INSTRUCTIONS の1行で挙動が変わったので、説明文の書き方の影響の大きさを実感
  - 承認を挟むと、実行は「止まる → 外から結果を渡して再開する」2回の `run_sync` に分かれる。会話履歴を渡し直して続きから再開する作りは、第1回の `--chat` で履歴を自分で持ったのと同じ考え方。
  - 拒否したあとの回答では、用語集を引かずに「関連：第4回または第5回など」と書かれた（LoRA は第2回）。INSTRUCTIONS の「用語集を確認してから答える」が、承認後・拒否後の続きの回答では守られない場合があることを認識うべき。
  - 記録の時刻が 02:49 になっていました。Codespaces が UTC で動いているためと推測。日本時間の記録にするにはタイムゾーンを指定する必要があります。
  - 疑問：第5回の MCP 経由のツールでは、承認が必要かどうかをサーバー側とクライアント側のどちらで決めるのがよいか疑問に思った
