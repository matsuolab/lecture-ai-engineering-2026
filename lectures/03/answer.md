# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  同じ質問「AIE2026の講座の宿題にある「3レベル」とは何ですか？」を app.ask と app.agent に投げて比べた。
  - 第1回（app.ask）: 講座の内容は確認できないと断ったうえで、「難易度を段階的に分けた課題システム」という一般論で、レベル1〜3の中身（穴埋め、条件分岐やループなど）を具体的に書いた。これらは用語集にない内容で、「どれか1つで完了」「原則採点しない」にも触れていなかった。回の表示もなかった。
  - エージェント: search_glossary で用語集を確認してから、「基礎・実装・発展の3段階で、どれか1つ取り組めば完了、原則採点しない」と答え、最後に「関連する回：第1回」を示した。
  - 用語集（homework-levels, lecture: 1）と照らすと、エージェントは構成・完了条件・採点・回が一致した。違ったのは、各レベルにモデルが足した括弧書きだけだった。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  質問「LoRAとは？」で `search_glossary({'query': 'LoRA'})` が1回呼ばれた。
  質問「LoRAについて学んだので、学習記録を保存して」では、`search_glossary({'query': 'LoRA'})` の後に `save_learning_log({'topic': 'LoRA', 'summary': '...'})` が呼ばれた。
- 1つの質問での LLM 呼び出し回数（`requests`）：
  「LoRAとは？」は requests=2（検索の依頼 → 結果を見て回答）。
  保存を頼む質問は、承認を挟むため2回に分かれ、1回目の実行が requests=2、2回目の実行が requests=1、合計3だった。
- 追加したツールと、docstring に書いた説明：
  `save_learning_log(topic, summary)`。docstring は「学習の記録を learning_log/ フォルダにファイルとして保存する。『今日の学習を記録して』『ログに残して』のように、利用者が学習内容の保存を明示的に求めたときだけ使う。保存の前に利用者の承認が入る。」
  （`make_quiz` は未実施）

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - `app/tools.py` に `save_learning_log(topic, summary)` を追加した。保存先は `learning_log/` で、ファイル名はモデルに決めさせず日時から作る（任意のパスに書かせないため）。topic か summary が空なら保存しない。
  - `app/agent.py` で `requires_approval=True` を付けて登録し、`output_type=[str, DeferredToolRequests]` に変更した。
  - `ask_approval` と `run_with_approval` を追加した。承認待ちで止まったら CLI で y/N を聞き、結果を `deferred_tool_results` に渡し、`message_history` を引き継いで続きを実行する。
  - INSTRUCTIONS に「学習の記録を保存したいと頼まれたら save_learning_log を使う」を1行足した。
- 結果：
  質問は「LoRAについて学んだので、学習記録を保存して」。
  - (A) `y` で承認：`[承認待ち] save_learning_log({'summary': '...', 'topic': 'LoRA'})` が表示され、承認後に `learning_log/20261109_061307.md` が保存された。ファイルの中身は、承認画面に表示された summary と一致していた。モデルは「保存しました」と回答した。requests は 2 + 1 = 合計3。
  - (B) `N` で拒否：同じ承認待ちが出て、`[tool return] save_learning_log -> 利用者が実行を断りました` となり、ファイルはできなかった。モデルは「承認が得られなかったため保存をキャンセルしました」と答え、LoRA の説明は続けた。requests は 2 + 1 = 合計3。
  - (C) 保存を頼まない（「LoRAとは？」）：`search_glossary` だけが呼ばれ、承認待ちは出なかった。requests は 2。
  - `--list-tools` に `save_learning_log` と docstring が表示された。`pytest -q` は 11 passed。
  - 
  ### (A) y で承認

[承認待ち] save_learning_log({'summary': '事前学習済みの重みを固定し、低ランク行列のパラメータのみを効率的に学習するPEFT手法であるLoRAについて学びました。', 'topic': 'LoRA'})
このツールを実行してよいですか？ [y/N]: y

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, ...
[tool call]   save_learning_log({'summary': '...LoRAについて学びました。', 'topic': 'LoRA'})
[tool return] save_learning_log -> 20261109_061307.md に保存しました。…
[usage 1回目の実行] ... requests=2, tool_calls=1
[usage 2回目の実行] ... requests=1, tool_calls=1

### (B) N で拒否

[承認待ち] save_learning_log({'summary': '...', 'topic': 'LoRA'})
このツールを実行してよいですか？ [y/N]: N

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool return] search_glossary -> [{"term": "LoRA", ...
[tool call]   save_learning_log({'summary': '...', 'topic': 'LoRA'})
[tool return] save_learning_log -> 利用者が実行を断りました…
[usage 1回目の実行] ... requests=2, tool_calls=1
[usage 2回目の実行] ... requests=1

### (C) 保存を頼まない(「LoRAとは？」)

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool return] search_glossary -> [{"term": "LoRA", ...
[usage] ... requests=2, tool_calls=1

- 気づき・疑問：
　-   - 用語集を検索するツールを持たせると、「3レベル」のような講座固有の言葉に、用語集どおりの定義で答えられた。ただし、用語集にない補足（「応用力の養成」など）をモデルが足すことがあり、検索結果と回答を照らして確かめる必要があると感じた。
  - 承認が必要なツールが呼ばれると、実行はそこで一度止まり、出力は文字列ではなく `DeferredToolRequests` になる。`output_type` に加えないと受け取れない。
  - 保存を頼む質問は LLM を合計3回呼んだ(1回目の実行 requests=2: 検索の依頼→保存の依頼、2回目の実行 requests=1: 承認後の最終回答)。保存を頼まない「LoRAとは？」は requests=2 だった。承認を挟むと実行が2回に分かれる。
  - `[usage]` は最後の実行分だけなので、質問全体の requests は各回を足す必要がある。最初は気づかなかった。
  - (A) の1回目の実行は requests=2 で、承認の前にすでに LLM のループが1周していた。まず search_glossary で確認し、その結果を見てから save_learning_log を依頼している。
  - topic と summary はモデルが決めるので、同じ質問でも実行ごとに文面が変わった。承認画面に引数が出るので、利用者は保存内容を見てから y を押せる。実際、(A) で保存されたファイルの中身は、承認画面の summary と一致していた。ここが承認を挟む意味だと感じた。
  - 拒否すると `ToolDenied` のメッセージがモデルに渡り、モデルは「承認が得られなかったため保存をキャンセルしました」と回答を変えた。
  - 最初の拒否テストで N を入れ忘れて y にしてしまい、2つ目のファイルが保存された。入力を間違えると実際に保存されるので、承認画面の確認が大事だと実感した。その後 N で再実行し、拒否の動作を確認した。
  - 疑問: 承認待ちで実行が止まっている間、会話の状態はどこに持たれているのか。今回は `message_history` を渡して続けたが、実際のアプリではどう管理するのか。