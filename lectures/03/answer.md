# 第3回 解答

> **実行環境について**: 課題は Google Colab ではなく、ローカルマシンの **DGX Spark（NVIDIA GB10）** で実行した。
> Python 環境は `~/.venv`（Python 3.12.3）を使用し、リポジトリの `pyproject.toml` に合わせて
> `pydantic-ai-slim[google,mcp]==2.57.0` / `google-genai==2.31.0` / `pytest`（発展 a 用に `google-adk==2.13.0` も）を追加インストールした。
> 既存の第2回環境（torch 2.11.0+cu130 / transformers 5.18.0）への影響はなかった。
> `uv run` の代わりに `/home/nako/matsuo/.venv/bin/python -m app.agent ...` で実行している（実行コードは同一）。
> モデルは既定の `gemini-3.5-flash-lite`。API キーはリポジトリ直下の `.env`（`.gitignore` 済み）に置き、実行時に環境変数へロードした。
> 生の出力原文は `lectures/03/work/`（`ex01_ask.txt` / `ex01_agent.txt` / `ex02_trace.txt` / `ex03_quiz.txt` / `pytest.txt` / `adk_*.txt`）に保存してある。

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - **素のLLM（`app.ask`）**: 「lecNN-start タグ」を知らないので「私の知識ベースには含まれていません」と前置きしたうえで、「NN＝ニューラルネットワークの略だろうから Lecture NN の開始を示す目印では」という**一般論からの推測**を3つ並べて断定気味に答えた。講座の実際（Git タグで開始コードを取る仕組み）とは違う説明だった（`work/ex01_ask.txt`。応答 6.48 秒、入力 23 / 出力 323 トークン）
  - **エージェント（`app.agent`）**: `search_glossary` を呼んで用語集を引き、**「AIE2026 の講座リポジトリで各回の演習開始時点のコードに付けられる Git タグ（例: `lec03-start`）」と正確に回答**し、末尾に関連回（第1回）も示した（`work/ex01_agent.txt`）
  - つまり第1回の「講座に固有のことは分からない／もっともらしい嘘をつく」問題が、ツール（用語集検索）を1つ足すだけで解消した
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「LoRAとQLoRAの違いは？」に対して:
    - `[tool call] search_glossary({'query': 'LoRA'})`
    - `[tool call] search_glossary({'query': 'QLoRA'})`
  - 2つの用語を**別々に**検索してから比較して答えている。`[tool return]` で用語集の JSON（term / lecture / definition / related）がモデルに返っているのが読める（`work/ex02_trace.txt`）
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - **`requests=2`**（1回目でツールを呼ぶことを決め、2回目で結果を見て回答文を生成）。`tool_calls=2`、入力 1,444 / 出力 184 トークン、コスト約 $0.0009（`RunUsage(cost=Decimal('0.0008932'), ...)`）
  - 1つの質問でも LLM は複数回呼ばれる＝「モデル+ループ」が回っていることが `usage` から確認できた
- 追加したツールと、docstring に書いた説明：
  - `app/tools.py` に `make_quiz(lecture: int) -> str` を追加し、`app/agent.py` の TODO の場所に `agent.tool_plain(tools.make_quiz)` で登録した
  - docstring: 「**指定した回（1始まりの整数）の用語から1つを選び、確認問題を1問作る。「第2回の内容から確認問題を1問出して」のように、学習の定着を確認したいときに使う。問題文・用語・答え（用語集の定義）を JSON で返す。答えは、学習者が自分の言葉で答えた後に開示すること（問題と一緒に答えを見せない）**」
  - 実装: `data/glossary.json` から該当回の用語を抽出して `random.choice` で1語選び、`{"question": "「〇〇」とは何か、自分の言葉で説明してください。", "term": ..., "answer": 定義, "related": [...]}` を JSON で返す。回が無い場合は用意されている回の一覧を返す
  - docstring の「答えを先に見せない」は効いていて、実際の実行（「第2回の内容から確認問題を1問出して」）では `make_quiz({'lecture': 2})` が呼ばれ、「**LoRA**」とは何かという問題だけを出し「答えがまとまったら、ぜひ教えてくださいね！」と答えを隠した（`work/ex03_quiz.txt`、requests=2 / tool_calls=1）
  - `--list-tools` で 3 ツール（search_glossary / get_lecture_summary / make_quiz）がモデルに見えていることを確認。テストも `tests/test_tools.py` に2件追加（該当回の用語から選ぶこと／存在しない回は「ありません」を返すこと）。**`pytest -q` は 16 passed**（`work/pytest.txt`）

## 宿題

- 取り組んだレベル：**発展（a）**（同じエージェントを Google ADK で作り直し）
- やったこと：
  - `lectures/03/work/adk/learning_agent/`（`__init__.py` + `agent.py`）に ADK 版を作成。**ツールは `app/tools.py` の3関数をそのまま再利用**、`INSTRUCTIONS` も Pydantic AI 版と同じ文字列を使った（= モデルとツールを共有し、組み立て方だけ比較する）
  - ルートエージェントは宣言1つ: `root_agent = Agent(name="learning_agent", model="gemini-3.5-flash-lite", description=..., instruction=INSTRUCTIONS, tools=[search_glossary, get_lecture_summary, make_quiz])`。Pydantic AI 版のような `agent.tool_plain(...)` の逐一登録・実行時のモデル指定が不要
  - 実行確認: `adk run`（ターミナル対話、`work/adk_run.txt`）と `adk web`（開発 UI、`http://127.0.0.1:8000`、起動して `/list-apps` に `learning_agent` が現れることを確認）。API キーは `GOOGLE_API_KEY` を ADK が agent の親フォルダから上に向かって `.env` を自動探索して読む（repo ルートの `.env` に `GOOGLE_API_KEY` を追記して解決）
  - ツール呼び出しの記録（`--trace` の ADK 相当）は `adk run` の標準出力には出ないため、`Runner` を直接回してイベント（`function_call` / `function_response` / `usage_metadata`）を列挙するスクリプト `work/adk_trace.py` を書いて取得した（`work/adk_trace.txt`）
- 結果（比較）：

  | | Pydantic AI 版（`app/agent.py`） | ADK 版（`work/adk/learning_agent`） |
  |---|---|---|
  | エージェント定義 | `Agent(instructions=...)` を作り `agent.tool_plain(fn)` を1つずつ登録 | `Agent(name, model, instruction, tools=[...])` に宣言時にまとめる |
  | ツール定義 | 関数の docstring + 型ヒント | **同じ**（`app/tools.py` を無変更で再利用できた） |
  | モデルの指定 | `run_sync(..., model=build_model())` と**実行時に**渡す（テストで TestModel に差し替えやすい） | エージェント**宣言時に**文字列で渡す |
  | 実行方法 | 自分の `main()` で `run_sync` | `adk web` / `adk run` / `Runner` が提供される |
  | ループ | フレームワーク内蔵（意識しない） | 同じく内蔵（Runner が担う） |
  | trace の見え方 | `--trace` オプションを `print_trace` として自前実装（tool call / return / usage を3行形式で表示） | 開発 UI にイベントストリーム表示が内蔵。CLI では出ないので、イベントを列挙すると `[tool call] search_glossary({'query': 'LoRA'})` の形で取れる |
  | usage の見え方 | `RunUsage(requests=2, input_tokens=1444, output_tokens=184)` — **requests＝LLM 呼び出し回数**が明示される | `usage_metadata`（prompt 1,094 / output 144）はあるが、requests 相当はイベントの回数として間接的に見える |
  | ツール戻り値の扱い | ツールの返り値（文字列）がそのまま返る | `{'result': '<文字列>'}` に包まれて返る |
  | 同じ質問の回答 | 用語集ベースで正確（第2回を引用） | ほぼ同じ内容・同じ引用元で回答（`work/adk_run.txt` / `adk_trace.txt`） |
  | 同じ質問のトークン | 入力 1,444 / 出力 184 | prompt 1,094 / output 144（フレームワークでシステムプロンプトの構成が違い、プロンプト長と回答の詳しさに差が出た） |

  - `adk web` の見え方: ブラウザの開発 UI でエージェント一覧（`/list-apps` で `["learning_agent"]` を確認済み）から選び、チャット形式で対話できる。各応答はイベント単位で流れ、モデル応答・ツール呼び出し・トークン使用量が時系列で見られる（Runner のイベント列挙と同じものの可視化）。セッションは InMemory サービスに保存され、セッション ID 単位で履歴が続く
- 気づき・疑問：
  - **「エージェント = モデル + ループ + ツール」のうち、モデルとツールはフレームワークをまたいで共有できた**。docstring + 型ヒントがツール定義になる考え方、指示文を文字列で渡す考え方は両者で同じ。違うのは「組み立てと実行のインターフェース」だけで、ここがフレームワークの選択ポイントになる
  - **道具の厚みが逆だった**: Pydantic AI はライブラリとして薄く、trace・usage・CLI を自分で書く（= 中身が見える。学習向き）。ADK はエージェントを「フォルダ + `root_agent`」で表現し、開発 UI・セッション管理・実行サーバーまで付属していて、`adk web` を開けばすぐ対話できる（= 運用向き）。裏で走っているのは同じ Runner のイベントループなので、課題の「エージェントの正体はループ」がどちらでも確認できた
  - **ツールの戻り値の包み方が違う**（ADK は `{'result': ...}` に包む）など、細部の差分はあるが、モデルの回答の質にほぼ差は出なかった。同じツール・同じ指示なら、どちらでも「講座の用語集に基づいて答える」というエージェントの振る舞いは再現された
  - 疑問: ①API キーの受け渡しの暗黙度が違い、ADK は環境変数名（`GOOGLE_API_KEY`）と `.env` 自動探索の挙動（CLI は読むが `Runner` 直叩きでは読まない）を知らないと「No API key」で詰まった。②プロンプトの構成（システムプロンプトの内容）がフレームワークで違うため、トークン数や回答の詳しさが変わる。「同じエージェント」を作っても完全に同一の出力にはならない点は、評価を設計するときに効いてきそう

