# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：回答のトークン数が大幅に減少し、端的に２文でLoRAとは及びQLoRAとはという問いに回答していた。また、関係する回が2回であるというような出力も追加された。もっとも、回答時間は6秒ほどと結構伸びた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[usage] RunUsage(cost=Decimal('0.0008338'), details={'text_prompt_tokens': 1196}, input_text_tokens=1196, input_tokens=1196, output_tokens=190, requests=2, tool_calls=2)
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：
　make_quizeツール→指定された回の用語からランダムに一つ選び、問題・答えをJSONで返す。また、該当する用語がない場合は存在しないとメッセージを返す。
　指定した回の学習内容を確認したいときに、用語の意味を問う問題を1問作る。
    用語集からその回の用語をランダムに1つ選び、問題と答えを返す。講義の用語を
    確認する問題を求められたときに使う。


## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
１：基礎
やったこと：instructionsの内容の変更
用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。という記述を削除した
回答の最後に関係する回のサマリーをget_lecture_summary を使って出力する。という記述を追加した
質問： " 第2回の内容から確認問題を1問出して
結果：変更前：--- trace ---
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> {"lecture": 2, "term": "LoRA", "question": "「LoRA」の意味は？", "answer": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな…
[usage] RunUsage(cost=Decimal('0.0004496'), details={'text_prompt_tokens': 957}, input_text_tokens=957, input_tokens=957, output_tokens=65, requests=2, tool_calls=1)
変更後：--- trace ---
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> {"lecture": 2, "term": "事前学習", "question": "「事前学習」の意味は？", "answer": "大量の汎用テキストで、次のトークンを予測するようにモデルを学習させる最初の段階。言語の知識や一般的な常…
[tool call]   get_lecture_summary({'lecture': 2})
[tool return] get_lecture_summary -> # 第2回 ファインチューニングとLoRA
[usage] RunUsage(cost=Decimal('0.0021050'), details={'text_prompt_tokens': 1975}, input_text_tokens=1975, input_tokens=1975, output_tokens=605, requests=3, tool_calls=2)
気づき・疑問：まず大きな変更点として回答の最後に関係する回のサマリーをget_lecture_summary を使って出力する。という記述を追加したおかげで質問を変更しなくても毎回関係する回のサマリーを出力してくれるようになった。また、変更前はLoRAについての質問だったが、変更後は事前学習の意義についての質問になっていた。これは用語集を確認するという最初のインストラクトが抜けていても、make_quizeというツールの中で実際に指定回の用語から選ぶという動作が実行されているために、あまり影響はなかったのではないかと考えられる。
２：実装
やったこと：app/tools.pyにsave_learning_log(lecture, reflection) を追加した。具体的にはlearning_log/ にMarkdown保存し、空の記録は保存しないようにした。また、app/agent.pyにrequires_approval=True で登録し、承認待ちを扱う DeferredToolRequests に対応した。
結果：テストは通過し、承認が必要であるようになった。
[save_learning_log]
  学習内容を記録したいときに、利用者の確認後に学習記録を保存する。
  
  指定した回についての気づきや疑問を learning_log/ に保存する。
  保存を実行する前に、必ず利用者の承認を得る必要がある。
  引数: {"lecture": {"type": "integer"}, "reflection": {"type": "string"}}
気づき・疑問：承認要求がagent側で実装するというのがなかなか気づきにくかった。また、テストについても１保存できること２空の記録を拒否すること３保存前に承諾が必要であることをプロセスに分解してコード化する必要があって難しかった・
３：発展（b）
やったこと：Piの公開システムプロンプトと、`app/agent.py` の `INSTRUCTIONS` を読んで比較した。また、Piと自作エージェントに質問し、ツールの使われ方を確認した。
結果１（システムプロンプトとの比較）：
pi：目的がコーディング作業で、ファイル操作及びコマンド実行が可能。安全性は作業内容に応じて制約が課されている。ツールはread/write/edit/bashがある。
自作エージェント：目的が講座の学習支援で、ファイル操作は学習記録のみ可能で可能で、コマンド実行は不可能。また、学習記録保存時に承認が必要となっている点で安全性が確保されている。ツールとしては、用語検索、講義要約、クイズ、学習記録がある。
結果２（質問の比較）：→質問”第三回では何を学びますか？”
自作エージェント：--- trace ---
[tool call]   get_lecture_summary({'lecture': 3})
[tool return] get_lecture_summary -> # 第3回 AIエージェント
→４個を箇条書きにして簡潔に説明していた
pi:ほぼ同じ感じ。リポジトリ内のファイルに準拠している。
気づき：
共通点は、モデルに役割や行動方針を与えること、ツールを使ってモデル単体ではできない処理を実行するそしてツールと会話のループで作業を進めること
相違点は、Piはコーディング向けで、ファイル編集やコマンド実行を行が、自作エージェントは講義学習向けで、用語検索や講義要約を行うこと、そしてPiはツール実行時に毎回確認しないが、自作エージェントは学習記録の保存に承認を要求することである。承認の有無が自身で設定できる点で自作エージェントの方が優れているかもしれない。

