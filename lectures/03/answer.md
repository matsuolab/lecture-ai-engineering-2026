# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：
- 1つの質問での LLM 呼び出し回数（`requests`）：
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：

### 発展(a)：ADKで作り直す

- 取り組んだレベル：発展(a)
- やったこと：
  - adk_agent/glossary_agent/ にADK版を作成した。
  - 元のINSTRUCTIONS、search_glossary、get_lecture_summaryを直接再利用した。
  - モデル設定も共有し、両方ともgemini-3.5-flash-liteで比較した。
  - app/のファイルは変更していない。

- 結果（書き方の比較）：
  - Pydantic AIではinstructionsで指示を渡し、tool_plainでツールを登録する。
  - ADKではinstructionとtoolsのリストをAgentに渡す。
  - Pydantic AI版はrun_syncで実行し、ADK版はroot_agentを定義してadk runで実行した。

- 結果（回答の比較）：
  - 両方に「LoRAとQLoRAの違いは？」と質問した。
  - 両方とも、LoRAは低ランク行列を学習し、QLoRAはベースモデルを量子化したうえでLoRAによる学習を行うと説明した。
  - 両方とも最後に「関係する回：第2回」と示した。
  - Pydantic AI版は各用語の説明から始まった。ADK版は最初に主な違いを一文で示し、アダプタを小さなファイルで保存できる点にも触れた。
  - Pydantic AI版のtraceではsearch_glossaryがLoRAとQLoRAに対して各1回呼ばれ、requests=2、tool_calls=2だった。
  - ADK版は通常のCLI表示で回答を確認したため、ツールの呼び出し回数・引数は未確認。

- 気づき・疑問：
  - 指示文とツール関数を共通化し、エージェントの組み立て部分を差し替えられることが分かった。
  - 同じモデル・指示・ツールでも、説明の順番や詳しさに違いがあった。
  - Pydantic AI版は1回、ADK版は同じ会話内で複数回質問した。会話履歴の条件も異なるため、回答の違いがフレームワークによるものか、履歴や生成のばらつきによるものかは断定できない。
