# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  同じ質問「AIE2026の講座で使う『lecNN-start タグ』とは何ですか？」を両方に投げた。
  `app.ask`（ツールなし）は「講義の開始地点を示す合図らしい」といった一般論の推測に留まり、
  「教材を確認するか講師に質問して」と逃げる回答だった。`app.agent` は `search_glossary` を
  呼んで用語集の定義を引き、「講座repoで各回の演習開始時点のコードに付けているGitタグ
  （例：lec03-start）。前の回が終わっていなくてもタグからブランチを切れば始められる」と、
  この講座固有の正確な内容を即答した。ツール（外部知識）の有無が回答品質を決定的に変えることが分かる。

- `--trace` で見えたツール呼び出し（ツール名と引数）：
  「LoRAとQLoRAの違いは？」に対し、`search_glossary("LoRA")` と `search_glossary("QLoRA")`
  の2回の呼び出しを確認した。モデルは質問を分解し、比較対象の2用語をそれぞれ用語集で引いている。

- 1つの質問での LLM 呼び出し回数（`requests`）：
  `requests=2`（ツール呼び出し指示の1回 + ツール結果を見て最終回答を書く1回）。
  ツールを使う質問は素のLLMの1回呼び出しより LLM 呼び出しが増える＝コスト・応答時間が増える。

- 追加したツールと、docstring に書いた説明：
  `make_quiz(lecture: int)` を `tools.py` に追加し、`agent.tool_plain(tools.make_quiz)` で登録。
  docstring には「指定した回の用語から1つを選び、確認問題と答えを返す。
  『確認問題を出して』と言われたときに使う」旨を書いた。
  実行「第2回の内容から確認問題を1問出して」→ `make_quiz({'lecture': 2})` が呼ばれ、
  「『ランク（LoRAのr）』の意味は？」という問題を出した（`requests=2`, `tool_calls=1`）。

## 宿題

- 取り組んだレベル：発展（(a) 同じエージェントを Google の ADK で作り直す）

- やったこと：
  `lectures/03/adk_agent/` に、Pydantic AI 版（`app/agent.py`）と同じ INSTRUCTIONS・
  同じ3ツール（search_glossary / get_lecture_summary / make_quiz）を持つエージェントを
  `google.adk.agents.Agent` で実装した（google-adk 2.13.0、依存は `adk` グループに分離）。
  ツール関数は `app/tools.py` をそのまま共有した。
  `adk run` で対話実行し、`adk web` の dev UI でイベント・トレースを確認した
  （`adk_web_ui.png` に証跡）。

- 結果：
  「LoRAとQLoRAの違いは？」→ Events パネルに `search_glossary("LoRA")` / `search_glossary("QLoRA")`
  の2イベントが並び、回答本文は Pydantic AI 版と同等の内容（第2回）を返した。
  「第2回の内容から確認問題を1問出して」→ `make_quiz(2)` が呼ばれ、問題のみを提示して
  答えを伏せる応答を得た。

- 気づき・疑問：
  - 書き方の差は小さい。Pydantic AI は `Agent(instructions=...)` + `tool_plain(fn)` で1行ずつ登録、
    ADK は `Agent(model=..., name=..., instruction=..., tools=[...])` と宣言的に1箇所で書く。
    どちらも「関数＋docstring＋型ヒント」をツール定義として読む点は共通で、
    ツール側のコードは一切書き換えずに共有できた。
  - `adk web` の見え方は強い。Pydantic AI では `result.all_messages()` を自分で辿って
    `ToolCallPart`/`ToolReturnPart` を print する必要があるが、ADK dev UI はイベントごとに
    カード（bolt=呼び出し・check=返却）として時系列表示され、State・Artifacts・Traces・
    Evals のタブまで備わる。学習・デバッグ用途では差が大きい。
  - 一方で ADK はセッションDB（`.adk/session.db`）など裏側の状態管理が自動で入り、
    「薄いハーネス」ではなくフル機能の実行環境という性格が分かる。Pydantic AI は
    必要最小限で、TestModel による API 不要の配線テストが軽い。
  - 疑問：ADK の INSTRUCTIONS（単数形 instruction）と Pydantic AI の instructions で
    システムプロンプトの組み立て方が内部でどう違うか（ADK は instruction を
    system_instruction としてそのまま渡す実装のようだが）は今後確かめたい。
