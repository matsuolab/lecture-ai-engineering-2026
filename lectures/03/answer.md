# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：Codespaces（`gemini-3.5-flash-lite`）で実行した
  - 「LoRAとQLoRAの違いは？」：`search_glossary({'query': 'LoRA'})` の 1 回だけ。QLoRA は検索せずに答えた。回答の QLoRA の説明は用語集とほぼ同じ内容だったが、INSTRUCTIONS の「答える前に必ず search_glossary で用語集を確認する」は、2 つ目の用語については守られていない
  - 「第2回の内容から確認問題を1問出して」：`make_quiz({'lecture': 2})` の 1 回。Hugging Face Hub の問題が選ばれた。回答には問題だけを出し、答え（ツールの結果には入っている）は「答えを知りたいときはいつでも聞いてください」として出さなかった。docstring に書いた使い方のとおりに動いた
  - 「LoRAとQLoRAの違いを調べて、学習の記録に保存して」：`search_glossary` を LoRA と QLoRA で 1 回ずつ、そのあと `save_learning_log`。同じ「LoRAとQLoRAの違い」でも、1 つ目の質問では QLoRA を検索しなかったのに、こちらでは検索した
- 1つの質問での LLM 呼び出し回数（`requests`）：上の 3 つはどれも 2 回（ツールを呼ぶ 1 回 → 結果を見て答える 1 回）。ツールを 2 つ同時に呼んでも、1 回の応答にまとめて入っていれば requests は増えない。入力トークンは 1,300〜1,550 で、そのほとんどは INSTRUCTIONS とツールの説明文
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture: int)`。指定した回の用語から 1 つをランダムに選び、「「用語」の意味は？」という問題と、答え（用語集の定義）を JSON で返す。用語の無い回を指定したら、用語がある回の一覧を返す。docstring には、使う場面（「第2回の内容から確認問題を出して」のように復習用の問題を頼まれたとき）と、使い方（まず問題だけを出し、答えは利用者が答えたあとか、求められたときに示す）を書いた。テストを 2 件追加した（その回の用語から出ること、用語の無い回の扱い）
  - 実際のモデルでの実行：`make_quiz({'lecture': 2})` が呼ばれ、問題だけを出して答えは伏せた（上の `--trace` の項目を参照）

## 宿題

- 取り組んだレベル：基礎・実装・発展（a と b の両方）
- やったこと：
  - 実装：`app/tools.py` に `save_learning_log(title, content)` を作り、`app/agent.py` で `requires_approval=True` を付けて登録した。`output_type` に `DeferredToolRequests` を加え、承認待ちで止まったら CLI で「実行してよいですか？ [y/N]」と聞き、答えを `DeferredToolResults` にして続きを実行する `run_with_approval` を書いた。断ったときは `ToolDenied` で「利用者が実行を断りました」とモデルに伝える。`INSTRUCTIONS` に「頼まれたときだけ save_learning_log で保存する」を 1 行足した
    - 保存先は `learning_log/YYYY-MM-DD.md`（その日のファイルに追記。`.gitignore` 済み）。ファイル名は日付だけで決め、モデルが渡す引数（title など）をパスに使わないようにした。`../` のような値で `learning_log/` の外に書かせないため
    - テスト `tests/test_learning_log.py`（TestModel、API キー不要）：ツール単体（追記・空の拒否・パスに使わない）と、承認の流れ（承認前は保存されない／y で保存される／n で保存されず、断ったことがモデルに伝わる）の 6 件
  - 基礎：`scripts/compare_prompts.py` を作った。`app/` を書き換えずに、パターンごとにエージェントを組み立て直し、1 か所だけ変えて同じ質問 2 つ（「LoRAとQLoRAの違いは？」「AIE2026の講座で使う「lecNN-start タグ」とは何ですか？」）を実行し、呼ばれたツールと引数・`requests`・回答を並べる
    - `base`：元のまま
    - `no_search_rule`：`INSTRUCTIONS` から「必ず search_glossary で用語集を確認する」の行を消す
    - `doc_bulk`：`search_glossary` の docstring の「用語を1つだけ入れる」を「まとめて入れる」（例: "LoRA QLoRA"）に変える
  - 発展 (a)：`adk_agent/glossary_agent/agent.py` と `__init__.py` を作り、同じ `INSTRUCTIONS` と `search_glossary`・`get_lecture_summary`・`make_quiz`（演習で追加）を ADK の `Agent` に渡した。`app/` は変えていない
  - 発展 (b)：Pi の公開されているシステムプロンプト（`packages/coding-agent/src/core/system-prompt.ts`）を読み、`INSTRUCTIONS` と比べた
- 結果：
  - 実装：テストは追加分（宿題 8 件、演習の make_quiz 2 件）を含めて 19 件すべて通った（`tests/test_mcp_server.py` の 2 件は、手元の PC に `uv` が無くサーバーを起動できないため除外。Codespaces では動く想定）
    - 既存の `test_base_tools_are_registered_and_called` が 1 件失敗した。TestModel は全ツールを呼ぶので `save_learning_log` も呼ばれ、承認待ちで止まって結果が戻らず、「ツール呼び出しの数 = 結果の数」が崩れたため。承認待ちの呼び出しを除いて数えるように直した。承認付きのツールを足すと、「呼んだら必ず結果が戻る」という前提が成り立たなくなる
    - 実際のモデルでの実行：`uv run python -m app.agent --trace "LoRAとQLoRAの違いを調べて、学習の記録に保存して"`（1 回目は 503 で失敗し、再実行した）
      - モデルは LoRA と QLoRA を検索したあと `save_learning_log` を呼び、実行は承認待ちで止まって「[確認] save_learning_log を実行しようとしています: {"title": "LoRA と QLoRA の違い", "content": "…"}」が表示された。見出しと本文は検索結果をまとめた妥当な内容だった
      - **不具合が見つかった**：日本語入力のまま全角の「ｙ」と答えたら、承認ではなく拒否として扱われ、保存されなかった。モデルには「利用者が実行を断りました」が伝わり、回答の最後で「保存を実行してもよろしいでしょうか？（まだ保存はしていません）」と聞き返した。拒否がモデルに伝わる流れ自体は正しく動いた
      - 直したこと：答えを NFKC で正規化して全角を半角にそろえ、「ｙ」も承認として扱うようにした。テストを追加した（全角の ｙ で保存される）
      - もう 1 つ直したこと：承認のあとの `[usage]` が `requests=1` で、承認後の実行の分しか数えていなかった。続きの実行に `usage=result.usage` を渡し、質問 1 つ分の合計を表示するようにした（テストを追加）
      - 直したあとの再実行（Codespaces で記入）：【y で保存されたか、`learning_log/` の中身、requests の合計】
  - 基礎（`uv run python -m scripts.compare_prompts --out lectures/03/compare_result.md` の結果を記入）

    | パターン | LoRAとQLoRA：ツール呼び出し（引数） | requests | lecNN-start：ツール呼び出し | requests | 回答の変化 |
    | --- | --- | --- | --- | --- | --- |
    | base |  |  |  |  |  |
    | no_search_rule |  |  |  |  |  |
    | doc_bulk |  |  |  |  |  |

    - 実行前に確かめたこと：`search_glossary` は `"LoRA QLoRA"` や `"LoRAとQLoRA"` のようにまとめて渡しても、LoRA と QLoRA の 2 件を返す。そのため `doc_bulk` では検索が 2 回 → 1 回に減っても、得られる情報は変わらないと予想する
  - 発展 (a)：ADK 2.14.0 で、`google-genai==2.31.0`（このリポジトリの固定版）と同時に入ることを確かめた。読み込むと、ADK も docstring と型ヒントからツールの説明を作り、モデルに渡す説明と引数（`query: string`、`lecture: integer`）は Pydantic AI 版と同じになった。API キーは `GEMINI_API_KEY` をそのまま読む
    - 書き方の違い：指示は `instruction=`（Pydantic AI は `instructions=`）、ツールは `tools=[関数]`（Pydantic AI は `agent.tool_plain(関数)`）。モデルは ADK では `Agent` を作るときに名前で決め、Pydantic AI では実行時に `run_sync(model=...)` で渡す（だからテストで TestModel に差し替えやすい）。会話のループと入力欄は `adk run` / `adk web` が受け持つので、argparse などを自分で書かなくてよい
    - 回答の比較（Codespaces で `PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent` を実行して記入）：【演習と同じ質問への回答の違い】
  - 発展 (b)：Pi のシステムプロンプトと `INSTRUCTIONS` の比較（Pi は 2026-11-08 時点の main を読んだ）

    | 観点 | Pi | 自分の `INSTRUCTIONS` |
    | --- | --- | --- |
    | 役割 | 「pi というハーネスの中で動くコーディング支援」 | 「AIE2026 の学習支援エージェント」 |
    | ツールの説明 | 使えるツールの一覧と短い説明を、設定に応じて自動で並べる | プロンプトには書かず、docstring に任せる（使う場面だけ指示に書く） |
    | ルール | 簡潔に答える、ファイルのパスをはっきり示す、ツールごとの使い方 | 答える前に必ず検索する、用語集に無いことは断定しない、関係する回を示す、宿題の答えは書かない |
    | 状況の情報 | 作業フォルダ、プロジェクトの指示ファイル、スキル、自分自身のドキュメントの場所 | なし（固定の文） |
    | 確認・安全 | 実行前の確認や、危ない操作への注意は書かれていない | 書かれていない（保存の確認はプロンプトではなくコードの `requires_approval` で強制） |

    - Pi を Codespaces で動かした結果（記入）：【`/model` で選んだモデル、試した指示と動き】
- 気づき・疑問：
  - 承認の入力を全角で打っただけで拒否になった。TestModel のテストでは「y」と「n」しか試しておらず、日本語入力という実際の使われ方を想定できていなかった。人に確認を求める部分は、モデルではなく人の入力のほうでつまずくことがある。拒否の扱いを「y 以外はすべて拒否」にしていたので、安全側に倒れて保存されなかったのはよかった
  - 承認を「プロンプトでお願いする」のではなく「コードで止める」と、モデルが指示を守らなくても保存は起きない。テストでも、TestModel が勝手に保存を呼んでも、承認前はファイルが作られないことを確かめられた。Pi のシステムプロンプトには確認の指示が無く、ツールは確認なしで動く。だから Codespaces の中で試すように言われている
  - Pi のプロンプトは中身が設定から組み立てられ、特定の分野の知識やルールは持たない（プロジェクトの指示ファイルやスキルで足す）。自分の `INSTRUCTIONS` は逆に、用語集を使うことや断定しないことなど、分野の振る舞いだけを書いている。汎用のハーネスと、特定の用途のエージェントの違いだと思う
  - ADK 版にも同じ `INSTRUCTIONS` を渡したので、ADK 版には無い `save_learning_log` に触れる 1 行が含まれる。記録を頼むと、無いツールを呼ぼうとするか試す価値がある（疑問）
