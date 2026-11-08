# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：外部の資料を参照して回答できる点に違いがあった。
- `--trace` で見えたツール呼び出し（ツール名と引数）： search_glossary({'query': 'LoRA'})
  search_glossary({'query': 'QLoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：２回
- 追加したツールと、docstring に書いた説明：してない

## 宿題

- 取り組んだレベル：発展（a）

- やったこと：
  Pydantic AI版と同じモデル設定、INSTRUCTIONS、
  search_glossary、get_lecture_summaryを使い、
  Google ADKで学習支援エージェントを作成した。
  両方に「LoRAとQLoRAの違いは？」と質問した。

- 結果：
  両方とも、LoRAとQLoRAの基本的な違いを説明できた。
  Pydantic AI版は、低ランク行列の積やアダプタの保存にも触れていた。
  ADK版は、冒頭で量子化の有無が主な違いだと示していた。

- 気づき・疑問：
  Pydantic AI版ではagent.tool_plainでツールを登録し、ADK版ではAgentのtoolsにリストで渡した。既存の指示と関数を再利用して、別のフレームワークでも動かせた。