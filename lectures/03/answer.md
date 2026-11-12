# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の `app.ask` は、質問をそのままモデルに投げて回答していたため、用語集や講義資料を参照しないことがあった。
  - エージェントでは `search_glossary` を先に呼び、`data/glossary.json` の定義を確認してから返答するようになっていた。そのため、回答の根拠が明確になり、用語の意味や関連回の説明が揃いやすくなった。
  - つまり、エージェントは「モデルだけ」でなく、外部の知識源を使って答える構成になっていると理解できた。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 例: `uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"`
  - 実際には、`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` がそれぞれ呼ばれていた。
  - `--trace` の `[tool call]` の行を見ると、モデルがどのツールをどんな引数で使ったかが一目でわかる。
  - この観察により、エージェントが「質問を受けて、まず道具で情報を調べてから答える」ことを確認できた。

- 1つの質問での LLM 呼び出し回数（`requests`）：
  - `requests` は、その run 内で LLM を何回呼んだかを表す。
  - 例として、LoRA と QLoRA の比較では、各用語の検索が2回行われ、`requests=2`、`tool_calls=2` のように表示された。
  - これは、1回の質問でも内部では複数のツール呼び出しと LLM 呼び出しがありうることを示しており、`usage` の意味を理解するのに役立った。

- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int) -> str`: 指定回の用語から確認問題を1問作るツール。
  - `search_glossary(query: str) -> str`: 用語を検索して定義と関連回を返すツール。
  - `get_lecture_summary(lecture: int) -> str`: 回ごとの要点を返すツール。
  - これらの docstring は、モデルが「どのツールを使うべきか」「どんな引数で使うべきか」を判断する説明文として機能しているとわかった。
  - そのため、説明文の書き方がモデルの挙動に直接影響することが、演習で実感できた。

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - `save_learning_log()` を追加し、`learning_log/` フォルダに `question` と `answer` を JSON 形式で保存するようにした。
  - `app/agent.py` で `agent.tool_plain(tools.save_learning_log, requires_approval=True)` として登録し、Pydantic AI の deferred approval を使えるようにした。
  - `app/agent.py` の `INSTRUCTIONS` を強化し、「make_quiz() の後には必ず save_learning_log() を呼ぶ」「自然言語で保存確認をしない」「承認フローを使う」と明記した。
  - `make_quiz()` の docstring も、「問題を作成したら必ず `save_learning_log(question=..., answer=...)` を使う」と書くようにした。
  - CLI で `--trace` を使って、承認フローが本当に発火することを確認した。

- 結果：
  - `uv run python -m app.agent --trace "第2回の内容から確認問題を1問出して"` を実行すると、`make_quiz()` が呼ばれた後、`save_learning_log()` の承認確認が出るようになった。
  - `y` を入力した場合は、`learning_log/` 配下に JSON が保存される。
  - `n` を入力した場合は、保存は拒否され、回答にも「保存は拒否されました」と出る。
  - 実際の `--trace`では、`[tool call] make_quiz(...)` のあとに `[tool call] save_learning_log({...})` が出ており、ツール approval の流れが正しく機能していることを確認できた。
  - 生成された JSON 形式は `{"question": "...", "answer": "..."}` で、保存先は `learning_log/learning_log_YYYYMMDD_HHMMSS_ffffff.json` の形式になる。

- 気づき・疑問：
  - 最初は指示文が弱く、モデルが自然言語で「保存してよいですか？」と返してしまうことがあった。これは、**ツールの説明、指示文、approval 登録の3つが揃っていないと、LLM が save tool を使わない** ことを実感した点で重要だった。
  - `requests` は「その run の LLM 呼び出し回数」であり、approval の再実行を含む全体の回数ではないことがわかった。`usage` を読むときは、その run 単位で解釈する必要がある。
  - 今回の実装では、保存の可否は利用者に委ねつつ、保存そのものは `save_learning_log()` を使うという設計にしたことで、保存の判断と保存処理が明確に分離された。
  - 学習ログの保存は取り消しにくい操作なので、approval フローを使って確認を挟むのが自然で、実際に安全な設計になったと思う。
