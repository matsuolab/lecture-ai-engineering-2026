# 第3回 解答

## 演習

### 1. 第1回（素のLLM）とエージェントの回答の違い

質問：AIE2026の講座の宿題にある「3レベル」とは何ですか？

| 観点 | 第1回 app.ask（素のLLM） | 第3回 app.agent |
|---|---|---|
| 答え方 | 「〜と推測します」と前置きし、一般論を回答 | search_glossary で用語集を確認してから回答 |
| レベルの名前 | レベル1〜3（基礎・応用・発展） | 基礎・実装・発展（用語集の定義と一致） |
| 完了条件 | 「全員レベル1は必須」など本講座に無いルールを補った | どれか1つで完了、原則採点なし |
| 根拠 | 「必ず記載されているはず」と断定 | 末尾に「（関連：第1回）」 |
| 出力トークン | 492 | 短い |

素のLLMは知らないことを一般論で埋めて断定する。エージェントは答える前に用語集を検索し、定義に基づいて答える。

### 2. --trace で見えたツール呼び出し（ツール名と引数）

質問「LoRAとQLoRAの違いは？」
- search_glossary({'query': 'LoRA'})
- search_glossary({'query': 'QLoRA'})

docstring の「query には用語を1つだけ入れる」に従い、1語ずつ別々に検索された。

質問「第2回の内容から確認問題を1問出して」
- make_quiz({'lecture': 2})

「第2回」から lecture=2 を選んだ。戻り値に answer も含まれていたが、モデルは問題文だけを出し、答えは伏せた。

### 3. 1つの質問での LLM の呼び出し回数（requests）

| 質問 | requests | tool_calls | input_tokens |
|---|---|---|---|
| LoRAとQLoRAの違いは？ | 2 | 2 | 1196 |
| 第2回の確認問題を1問出して | 2 | 1 | 896 |

1回目でツール呼び出しを決め、2回目で結果を受けて回答する。2つの検索は1回の応答で同時に依頼されたため、requests は3ではなく2だった。input_tokens はツールの戻り値を含むため、検索結果2件分の1問目の方が多い。

### 4. 追加したツールと、docstring に書いた説明

app/tools.py に make_quiz(lecture: int) -> str を追加し、app/agent.py で agent.tool_plain(tools.make_quiz) として登録した。

docstring：

    指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    lecture には回の番号（1始まりの整数）を入れる。

- load_glossary() から lecture が一致する用語を集め、random.choice で1つ選び、question・answer・lecture を json.dumps で返す
- 用語が無い回（lecture=0 など）は例外を出さず案内文を返す
- --list-tools で make_quiz と docstring が表示され、--trace で呼ばれ、pytest は11件 passed（--ignore=tests/test_ask.py）

### 気づき・疑問

- --list-tools の説明文は docstring そのもので、モデルはこれを読んでツールを選ぶ
- 第1回で app/ask.py に応答時間・トークン数の表示を足していたため、tests/test_ask.py の1件が出力順の違いで失敗した。追加したツールとは無関係だが、自分の改造が講座のテストとずれることがあると分かった

## 宿題

- 取り組んだレベル：基礎
- やったこと：
  INSTRUCTIONS と docstring を一度に1か所だけ変え、同じ質問を --trace 付きで実行して、変更前（演習の結果）と比べた。
  1. app/agent.py の INSTRUCTIONS から「必ず search_glossary で用語集を確認する」の行を削除
  2. app/tools.py の search_glossary の docstring を「用語を1つだけ入れる（例: "LoRA"）」から「用語をまとめて入れる（例: "LoRA QLoRA"）」に変更
  それぞれ実行後は元に戻した。
- 結果：

  実験1：INSTRUCTIONS の「必ず確認する」を削除

  | 質問 | tool call | requests | 回答 |
  |---|---|---|---|
  | LoRAとQLoRAの違いは？ | search_glossary 2回（'LoRA'、'QLoRA'） | 2 | 変更前と同じく定義どおり |
  | 「3レベル」とは？ | search_glossary 1回（'3レベル'） | 2 | 基礎・実装・発展、どれか1つで完了 |

  行を消しても検索をやめず、ツールの呼ばれ方・回答とも変更前と変わらなかった。

  実験2：docstring を「1つだけ」→「まとめて」

  | | 変更前 | 変更後 |
  |---|---|---|
  | tool_calls | 2 | 1 |
  | 引数 | 'LoRA'、'QLoRA' | 'LoRA QLoRA' |
  | requests | 2 | 2 |
  | input_tokens | 1196 | 1071 |
  | 回答 | 定義どおり | 定義どおり |

  docstring の例のとおり2語をまとめて1回で検索した。検索結果は変更前と同じ2件が返り、回答も定義に沿っていた。

- 気づき・疑問：
  - 実験1で検索をやめなかったのは、search_glossary の docstring にも「答える前に使うこと」と書いてあるため。指示は INSTRUCTIONS と docstring の2か所にあり、片方を消しても残った方が効く。
  - 実験2で「LoRA QLoRA」でも見つかったのは、ツール側の部分一致（名前が3文字以上なら query に含まれていれば当たり）が受け止めたから。docstring を変えた結果は、ツールの実装次第で変わるので、trace で確かめないと分からない。
  - docstring の例（"LoRA" / "LoRA QLoRA"）を変えただけで、モデルは引数の渡し方をその例に合わせた。docstring の例文は引数の形を決める強い手がかりになる。
  - 回答の末尾は「（関連：第2回）」「第1回」「関係する回：第2回」と実行ごとに書き方が揺れた。指示の内容は守られるが、表記までは固定されない。
  - 実験2の回答に「Low-Rank Adaptation」「Quantized LoRA」など用語集に無い語が含まれた。定義に基づきつつ、モデルの知識から補足が足されている。
  - 疑問：docstring の「答える前に使うこと」だけを消したら検索をやめるのか（実験3として未実施）。

  ## 宿題その２
  ### 実装：保存の前に確認を挟む（save_learning_log）

#### やったこと

| ファイル | 変更 |
|---|---|
| app/tools.py | `save_learning_log(title, content)` を追加。`learning_log/YYYYMMDD_HHMMSS.md` に `# title` と本文を書き、保存先パスを返す |
| app/agent.py | `Agent(..., output_type=[str, DeferredToolRequests])` に変更。`agent.tool_plain(tools.save_learning_log, requires_approval=True)` で登録 |
| app/agent.py `main()` | `result.output` が `DeferredToolRequests` の間、`ask_approvals()` でツール名と引数を表示して `[y/N]` を聞き、`DeferredToolResults.approvals[tool_call_id]` に `True` または `ToolDenied("利用者が保存を取りやめました")` を入れ、`message_history=result.all_messages()` と `deferred_tool_results` を渡して `run_sync` を再実行 |

確認コマンド：`uv run python -m app.agent --trace "第3回で学んだことを学習ログに記録して。内容は Pydantic AI の tool_plain でツールを登録する方法"`

#### 結果

| 段階 | 結果（--trace より） |
|---|---|
| 承認処理を入れる前 | 回答の代わりに `DeferredToolRequests(approvals=[ToolCallPart(tool_name='save_learning_log', args={'title': ..., 'content': ...}, tool_call_id=...)])` が表示されて終了。`[tool call] save_learning_log` はあるが `[tool return]` は無く、`learning_log/` は作られなかった。`[usage] requests=4, tool_calls=3`（承認待ちの1件は tool_calls に数えられていない） |
| 承認処理あり・`y` | `--- 承認が必要です ---` にツール名・title・content が表示され、`y` の後に `[tool return] save_learning_log -> 保存しました: learning_log/20261106_125327.md`。回答は「学習ログに保存しました」。trace には1回目の `get_lecture_summary`・`search_glossary` も残っている（message_history がつながっている）。`[usage] requests=1, tool_calls=1`（2回目の run の分だけ） |
| 承認処理あり・`n` | `[tool return] save_learning_log -> 利用者が保存を取りやめました`。回答は「保存が取り消されました。保存したい場合は改めて記録してとお知らせください」。ファイルは増えなかった。`[usage]` に tool_calls 無し |
| `uv run pytest -q --ignore=tests/test_ask.py` | 11 passed。`learning_log/` のファイルは増えなかった |

#### 気づき・疑問

| 項目 | 内容 |
|---|---|
| docstring に「承認を挟む」と書くと呼ばれなくなった | 最初の docstring に「実行前に利用者の承認を挟む」と書いたところ、モデルはツールを呼ばず、文章で「保存してよろしいですか？」と聞いて終わった（`[tool call] save_learning_log` 無し、requests=3）。「承認は呼び出し側のプログラムが自動で求めるので、ツールを呼ぶ前に確認する必要はない」に書き換えると、ツールを呼ぶようになり CLI の承認が出た。承認はプログラム側（requires_approval）の仕事なので、モデルには知らせないほうがよい |
| 見出しが二重になった | ツール側で `# {title}` を書く一方、モデルも content の先頭に `# ...` を入れたため、保存ファイルの見出しが2行重なった（2回とも）。docstring の content の説明に「見出し行はツール側で付けるので本文に含めない」と足したら、重ならなくなった。ツールの決め事は docstring に書かないとモデルには伝わらない |
| Args/Returns を書くと引数ごとの説明が付く | `--list-tools` で、save_learning_log の引数には description が付き、make_quiz（Args を書いていない）には付かなかった。docstring の Google 形式をフレームワークが構造として読んでいる |
| usage の数え方 | 承認後の `result.usage` は2回目の run の分だけ（requests=1）。全体の回数は1回目（requests=4）と足す必要がある。承認待ちや拒否されたツールは `tool_calls` に数えられない |
| 疑問 | `HandleDeferredToolCalls` という、run を止めずに同じプロセス内で承認を処理する方式が公式ドキュメントにある。CLI のような同一プロセスならそちらでもよさそうだが、止めて再実行する方式との使い分けの基準は何か |
  
  以上　2026/11/06