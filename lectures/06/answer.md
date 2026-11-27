# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：`glossary_search_glossary`（宿題のあとは `glossary_get_lecture_summary`・`glossary_make_quiz` も並ぶ。STEP 3・4 のあとは fetch・aws を足して計9個）
- STEP 2 の [tool call]：`[tool call]   glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]：`[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`（続けて `glossary_search_glossary({'query': 'MCP'})` も呼んだ）
- STEP 4 の [tool call]：`[tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'})` → `[tool call]   aws_aws___search_documentation({'search_phrase': 'Using versioning in S3 buckets', 'topics': ['general']})`
- 気づき・疑問：
  - コードを変えず、`app/mcp_servers.json` に2行足すだけで、Web の取得と AWS のドキュメント検索が使えるようになった。fetch は自分の PC で起動するサーバー、aws は URL に接続するだけのサーバーで、どちらもエージェント側からは同じ「ツール」に見える
  - ツールを足すだけで入力が増える。同じ用語集の質問でも、ツール3個のとき（宿題 b1）は入力 1,584 tokens、9個のとき（STEP 2）は 5,857 tokens だった。aws のツールは説明文が長く、使わない質問でも毎回モデルに渡る
  - fetch の説明文には「元々インターネットに接続できないと案内するよう言われていたが、このツールで接続できるようになった」という、モデルへの指示のような文が入っていた。説明文は他人が書いたプロンプトとしてそのままモデルに入るので、外部のサーバーを足すときは、ツール一覧で説明文を読んでから使うべきだと感じた
  - STEP 3 では、要約に必要のない `search_glossary('MCP')` も呼んだ。INSTRUCTIONS の「用語は答える前に用語集で確認する」に従ったと思われる。STEP 4 の1回目の検索は、ドキュメントではなく AWS のスキルが上位に来たため、英語の検索語で検索し直していた

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

**Gemini での結果**（gemini-3.5-flash-lite、各1回。回答と trace の全文は `lectures/06/results/homework_report.md`）

| 質問 | 知らせ方 | ツール呼び出し | 結果 |
|---|---|---|---|
| b1 第2回では何を学びますか？（基礎） | — | `get_lecture_summary(lecture=2)` | 第2回の要点（FT と LoRA、SFT、PEFT、QLoRA）で正しく回答 |
| i1 第2回のクイズを2問作って | — | `make_quiz(lecture=2, count=2)` | 「過学習」「QLoRA」の2問を、答えを隠して出題 |
| i2 第99回のクイズを作って | return | `make_quiz(lecture=99)` | 「第1〜13回まで」「作れるのは第1〜4回・第6回」と伝え、どの回にするか聞き返した |
| | raise | `make_quiz(99)` → `make_quiz(99, count=1)` | 理由が届かず、引数を少し変えて呼び直し、**実行が止まった**（`exceeded max retries count of 1`） |
| | ToolError | `make_quiz(lecture=99)` | return と同じ内容を伝えた |
| i3 第5回のクイズを作って | return | `make_quiz(lecture=5, count=1)` | 「第5回の用語はまだない」「作れる回」を伝えた |
| | raise | `make_quiz(5, count=1)` → `make_quiz(5)` | i2 と同じく、呼び直して**実行が止まった** |
| | ToolError | `make_quiz(lecture=5, count=1)` | return と同じ内容を伝えた |
| i4 第2回のクイズを10問作って | return | `make_quiz(lecture=2, count=10)` | 「最大5問」は伝えたが、**呼び直さずに、用語集にない問題を5問自分で作った**（後述） |
| | raise・ToolError | `make_quiz(lecture=2, count=5)` | 説明文の「1〜5」を読み、最初から5問で呼んだので、範囲外にならなかった |

- **return**：3種類の範囲外のどれでも、メッセージがそのまま届き、モデルは「なぜ作れないか」「次に何を選べるか」を正しく伝えた（i2・i3）
- **raise（ValueError のまま）**：モデルに届くのは `Error executing tool make_quiz` と `Fix the errors and try again.` だけ。理由が分からないので、`count=1` を足す・外すなど、意味のない呼び直しをして、2回とも実行全体が止まった
- **ToolError**：理由は届くので、今回は return と同じ結果だった。ただ扱いは「引数を直して呼び直せ」なので、モデルが1回でも呼び直すと raise と同じく止まる（API なしのテストで確認）。範囲外は呼び直しても直らないので、return のほうが安全
- 入力トークンは3方式ともほぼ同じ（約1,100〜1,150 tokens）。違いは「止まるかどうか」と「理由が届くかどうか」だった

### 残る失敗

- **i4（問題数10問）の return**：メッセージで「1〜5で指定して」と伝えたのに、モデルは `count=5` で呼び直さず、「正解率」「ドロップアウト」など**用語集にも第2回にもない問題を自分で5問作った**。メッセージが「できない理由」までで、「次にどう呼べばよいか（`count=5` で呼び直す）」を指示していなかったのが原因だと考える
- 直すなら、(1) メッセージに「`make_quiz(lecture=2, count=5)` で呼び直してください」と書く、(2) 6以上はツール側で5に切り詰め、「5問に減らした」と添えて返す、のどちらか。範囲外を伝えるだけでは足りず、次の一手まで書く必要がある
- raise と ToolError の i4 は、モデルが最初から `count=5` で呼んだので範囲外の比較になっていない。同じ質問でも、モデルの引数の選び方が毎回変わる

### 気づき・疑問

- ツールのエラーの扱いは、作る側（サーバー）とつなぐ側（pydantic-ai）の両方で決まっていた。MCP サーバーは想定外の例外の中身を外に出さず（中身はサーバーのログにだけ残る）、pydantic-ai はエラーを「呼び直せ」として扱い、1回までしか許さない。サーバーを作るときは、自分のコードだけでなく、その先でエラーがどう見えるかまで確かめる必要がある
- 「分かりやすいメッセージ」は、人が読んで分かる文ではなく、モデルが次の行動を決められる文だと感じた。i2・i3 は「作れる回」を並べたので聞き返しができたが、i4 は次の呼び方を書かなかったので、モデルが勝手に埋めた
- 疑問：説明文に「1〜5」と書いたことで、raise・ToolError の i4 では最初から範囲内で呼べた。範囲外のメッセージを工夫するより、説明文で範囲を伝えるほうが効くのか、何回か繰り返して確かめたい
