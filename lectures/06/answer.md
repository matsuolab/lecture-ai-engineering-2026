# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：
- STEP 2 の [tool call]：
- STEP 3 の [tool call]：
- STEP 4 の [tool call]：
- 気づき・疑問：

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎・実装（Omnicampus では「実装」を選択）
- AIの利用：実装・テスト・比較スクリプトの作成に AI を使った。実行と結果の確認は Codespaces で自分で行った

### やったこと

**基礎：`get_lecture_summary` を公開する**

- `app/mcp_server.py` の TODO の下に `get_lecture_summary` の公開を1行足した。エージェント側（`app/mcp_agent.py`・`app/mcp_servers.json`）は変えていない

**実装：`make_quiz` を作って公開する（第3回では作っていなかったので新しく作った）**

- 処理は `app/tools.py` に置き、`app/mcp_server.py` では公開だけを行う形に分けた（第3回の `app/agent.py` からも同じ関数を使える）
  - `build_quiz(lecture, count)`：用語集から指定した回の用語を `count` 個選び、「『○○』の意味は？」と答え（定義）の組にする。範囲外なら `QuizArgumentError` を投げる
  - `make_quiz(lecture, count=1)`：MCP で公開するツール。`build_quiz` の例外を受け取り、**分かりやすいメッセージを `return` で返す**
- 範囲外の3種類と、返すメッセージ（どこが範囲外か＋次に何を指定すればよいか）

| 範囲外 | 返すメッセージ |
|---|---|
| 存在しない回（第99回・第0回・負の数） | クイズを作れません: 第99回はこの講座にありません。この講座は第1〜13回です。クイズを作れる回: 第1回（26語）、第2回（12語）、第3回（13語）、第4回（7語）、第6回（7語）。 |
| 講座にはあるが、用語集に用語がない回（第5回など） | クイズを作れません: 第5回の用語はまだ用語集にありません。クイズを作れる回: …（同上） |
| 問題数 `count` が1〜5の外 | クイズを作れません: 問題数 count は1〜5で指定してください（指定された値: 10）。第2回の用語は12語あります。 |

- 説明文（docstring）には、使う場面・`count` の範囲・「答えはすぐに見せず、まず問題だけを出題する」・「範囲外のときは説明する文を返す」を書いた
- **return と raise の比較用**に、`app/mcp_server.py` に `--quiz-errors` を足した。ツールの名前と説明文は同じで、範囲外の知らせ方だけが違う
  - `return`（既定・提出する実装）：上のメッセージを `return` で返す
  - `raise`：同じメッセージの例外（`ValueError` の仲間）をそのまま投げる
  - `tool-error`：同じメッセージを MCP の `ToolError` として投げる
- テスト：`tests/test_lec06_quiz.py`（範囲外6通りのメッセージ、MCP 経由で一覧に3つのツールが出ること、知らせ方ごとにモデルへ届く内容）。`uv run pytest -q` で全件 pass
- 比較：`scripts/run_lec06_homework.py` で、同じ質問を同じモデルで実行し、`lectures/06/results/` に回答と trace を保存した

### 結果

**API を使わずに確かめたこと（テスト・偽モデルで、モデルに渡る内容をそのまま取り出した）**

| 知らせ方 | `[tool …]` の行 | モデルに渡る内容 | 同じ呼び出しを2回したとき |
|---|---|---|---|
| return | `[tool return]` | 返したメッセージがそのまま渡る | 2回とも普通の結果として渡り、実行は続く |
| raise（ValueError） | `[tool error]` | `Error executing tool make_quiz` と `Fix the errors and try again.` だけ。**理由（第1〜13回、作れる回）は届かない** | 「やり直し」の上限（1回）を超え、**実行全体が止まる**（`exceeded max retries count of 1`） |
| ToolError | `[tool error]` | `Error executing tool make_quiz: クイズを作れません: …` に続けて `Fix the errors and try again.` | raise と同じく実行が止まる |

- raise のとき、詳しい理由はサーバー側のエラー表示（`server_stderr.log` の Traceback）には残るが、モデルには届かない。MCP のサーバーが、想定外の例外の中身を外に出さないようにしているため
- 例外にすると、pydantic-ai は「引数を直して呼び直せ」という扱い（`RetryPromptPart`）にする。範囲外は呼び直しても直らないことが多いので、この用途には合わない

<!-- TODO: scripts/run_lec06_homework.py の実行後、Gemini での結果をここに書く -->

**Gemini での結果**（実行後に記入）

### 気づき・疑問

（実行後に記入）
