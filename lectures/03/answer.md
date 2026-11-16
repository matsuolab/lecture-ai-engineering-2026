# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：

〇素のLLMの回答
uv run python -m app.agent "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
[model] gemini-3.5-flash-lite
AIE2026の宿題における「3レベル」とは、宿題の難易度や取り組み方の構成のことです。

具体的には以下の3段階に分かれています：
1. **基礎**：講義内容の確認
2. **実装**：自分でコードを書く
3. **発展**：調査や試行

- `--trace` で見えたツール呼び出し（ツール名と引数）：
(aie2026-exercises) @ikatsuse-ui ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --trace "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
[model] gemini-3.5-flash-lite
AIE2026の宿題における「3レベル」とは、宿題の難易度や取り組み方の段階として用意されている**「基礎」「実装」「発展」**の3つのレベルのことです。

* **基礎**：講義内容の確認を中心とした問題
* **実装**：自分で実際にコードを書く問題
* **発展**：より踏み込んだ調査や新しい試みを行う課題

この3つのうち**どれか1つ**に取り組めば、その回の宿題は完了となります（原則として採点は行われません）。ご自身の興味や現在のレベルに合わせて選んでみてくださいね。

第1回

--- trace ---
[tool call]   search_glossary({'query': '3レベル'})
[tool return] search_glossary -> [{"term": "宿題の3レベル", "lecture": 1, "definition": "AIE2026の宿題の構成。「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階があり、どれか1つに取り組…
[usage] RunUsage(cost=Decimal('0.0006199'), details={'text_prompt_tokens': 783}, input_text_tokens=783, input_tokens=783, output_tokens=154, requests=2, tool_calls=1)

- 1つの質問での LLM 呼び出し回数（`requests`）：2回
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：手順４（make_quizの追加）と手順５（テスト）
- 結果：3つのテストコードの実行
(aie2026-exercises) @ikatsuse-ui ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --list-tools
モデルに見えているツール: 3 個

[search_glossary]
  講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。
  
  AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
  答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
  引数: {"query": {"type": "string"}}

[get_lecture_summary]
  指定した回（1始まりの整数）の講義の要点を返す。
  
  「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
  引数: {"lecture": {"type": "integer"}}

[make_quiz]
  指定回の用語で理解度を確認する問題と答えを作る。
  
  講座の特定回についてクイズを出したいときに使う。用語集からその回の用語を
  1つ選び、「用語の意味は？」という問題と、その用語の定義を返す。
  引数: {"lecture": {"type": "integer"}}

(aie2026-exercises) @ikatsuse-ui ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --trace "第2回の内容から確認問題を1問出して"
[model] gemini-3.5-flash-lite
第2回の内容から、理解度を確認するための問題です！

**【確認問題】**
Q. 「過学習（オーバーフィッティング）」とは、どのような状態を指すでしょうか？

（考えてみてくださいね。準備ができたら答え合わせをしましょう！）

関係する回：第2回

--- trace ---
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> 問題:「過学習の意味は？」
答え:学習データにだけ過度に適合し、未知の入力に対する性能が落ちる状態。学習に使わない検証データで性能を測って気づく。…
[usage] RunUsage(cost=Decimal('0.0004595'), details={'text_prompt_tokens': 890}, input_text_tokens=890, input_tokens=890, output_tokens=77, requests=2, tool_calls=1)
(aie2026-exercises) @ikatsuse-ui ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run pytest -q
.............                                                                                                                                                                      [100%]
13 passed in 4.41s


- 気づき・疑問：
演習資料の通りにcopilotに依頼すればコードはでき、テストも通りましたが、何をやっているのか、自分ではまだよくわかっていません。
