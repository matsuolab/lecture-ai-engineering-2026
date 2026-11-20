# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
　第1回はLLMの知識で回答するが、第3回では、LLMがsearch_glossaryを呼び出した結果を参考にして、LLMが回答するので、LLMの呼び出し回数が増加する。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
　uv run python -m app.agent --trace "過学習とエポックと学習率と誤差についておしえてください。"　
　とした場合
　　[tool call]   search_glossary({'query': '過学習'})
　　[tool call]   search_glossary({'query': 'エポック'})
　　[tool call]   search_glossary({'query': '学習率'})
　　[tool call]   search_glossary({'query': '誤差'})
　search_glossaryが、検索単語の引数で合計４回呼ばれた。
- 1つの質問での LLM 呼び出し回数（`requests`）：
　「過学習についておしえてください。」と質問した場合、requests=2であった。
- 追加したツールと、docstring に書いた説明：
　追加したツール
  　make_quiz
　docstring に書いた説明
  　"""指定した回の用語から 1つを選び、
  　確認問題と答えを返す。
  　「第2回の確認問題を出して」のように、
  　復習用の問題を求められたときに使う。
  """

## 宿題

- 取り組んだレベル：実践 
- やったこと：
- 基礎では
  INSTRUCTIONS
  に
  受講生が理解しにくそうな未解説の専門用語が含まれている場合は、自律的に再度 search_glossary を呼び出して深掘り調査を行うこと。
  を加えた。
- 結果：条件追加前は、過学習に対する回答をしたが、条件追加後は、epochについて深堀り調査を行い、epochに関する解説を交えた過学習の解説となった。evaluation-loopについても深堀り調査を行ったようであるが、LLMが回答に必須ではないと判断したのか、evaluation-loopの深堀り結果は、回答には反映されていない。
これにより、search_glossaryの呼び出し回数は１回から３回へ増加した。
また、input_tokenは948⇒2618 output_tokensは170⇒238へ増加した。

詳細は以下のとおり。
●条件追加前は
 (aie2026-exercises) @zuazua534 ➜ /workspaces/lecture-ai-engineering-2026 (lec03) $ uv run python -m app.agent --trace "過学習についておしえてください。"　
[model] gemini-3.5-flash-lite
**過学習（オーバーフィッティング）**とは、AIモデルが訓練（学習）データに対して過度に適合してしまい、学習に使っていない未知のデータ（テストデータや新しい入力）に対してうまく予測や対応ができなくなってしまう状態のことです。
例えば、過去問の答えを丸暗記しただけで、問題の本質を理解していないため、少し問題の出され方が変わると解けなくなってしまう状態に似ています。学習データに対する正答率は高いのに、実際の性能が低くなってしまうのが特徴です。
過学習を防ぐためには、学習データを増やしたり、訓練データ以外のデータ（検証データ）での性能を確認しながら学習を適切に止めたりする対策が行われます。
関連する回：第2回
--- trace ---
[tool call]   search_glossary({'query': '過学習'})
[tool return] search_glossary -> [{"term": "過学習", "lecture": 2, "definition": "学習データにだけ過度に適合し、未知の入力に対する性能が落ちる状態。学習に使わない検証データで性能を測って気づく。", "related": ["ep…
[usage] RunUsage(cost=Decimal('0.0007094'), details={'text_prompt_tokens': 948}, input_text_tokens=948, input_tokens=948, output_tokens=170, requests=2, tool_calls=1)

●条件追加後は
[model] gemini-3.5-flash-lite
**過学習（オーバーフィッティング）**とは、AIモデルが**学習データにだけ過度に適合してしまい、未知の入力（テストデータなど）に対する予測や性能が落ちてしまう状態**のことです。
具体的には、手元の学習データに対しては問題なく正解できるようになりますが、これまで見たことがない新しいデータを与えたときに、うまく対応できなくなってしまいます。
### 主な原因
- **学習のしすぎ（エポック数の増加など）**: 学習データ全体を何周も学習させる（エポックを増やす）ことで、モデルがデータの傾向だけでなく、ノイズや細かい癖まで丸暗記してしまうため起きやすくなります。
### 気づき方・対策
- 学習に使っていない**検証データ**を使ってモデルの性能を測定することで、過学習に気づくことができます。
（関連する回：第2回）
--- trace ---
[tool call]   search_glossary({'query': '過学習'})
[tool return] search_glossary -> [{"term": "過学習", "lecture": 2, "definition": "学習データにだけ過度に適合し、未知の入力に対する性能が落ちる状態。学習に使わない検証データで性能を測って気づく。", "related": ["ep…
[tool call]   search_glossary({'query': 'epoch'})
[tool return] search_glossary -> [{"term": "エポック", "lecture": 2, "definition": "学習データ全体を1周学習することを1エポックと数える。回数を増やしすぎると過学習しやすい。", "related": ["overfitting"…
[tool call]   search_glossary({'query': 'evaluation-loop'})
[tool return] search_glossary -> [{"term": "評価と改善のサイクル", "lecture": 1, "definition": "作る→測る→直すを繰り返す開発の進め方。AIアプリは出力が確率的に揺れるため、感覚ではなく評価データや指標で良し悪しを判断し、その結果…
[usage] RunUsage(cost=Decimal('0.0013804'), details={'text_prompt_tokens': 2618}, input_text_tokens=2618, input_tokens=2618, output_tokens=238, requests=4, tool_calls=3)

- 実践では、課題のとおり、save_learning_logで回答を保存するコードを作成した。
  データはlearning_logに保存されるようになった。

- 気づき・疑問：
- 基礎
　「過学習」について３回か検索したが、深堀りしたのは１回であった。
　検索数が発散しないように適切に条件を付与する必要があると思った。
- 実践
  学習記録を保存しますか？ [y/N]:が表示されないことが多いので、「質問とあなたが作成した回答を「必ず」」と加えると学習記録を保存しますか？ [y/N]:が表示されるようになった。
