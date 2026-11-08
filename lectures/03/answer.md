# 第3回 解答

## 演習

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の素のLLMは、用語集を検索せずに回答する。
  - エージェントは`search_glossary`を呼び出し、用語集を参照して回答する。
  - 今回のエージェントは、LoRAとQLoRAをそれぞれ検索してから回答した。

- `--trace`で見えたツール呼び出し：
  - `search_glossary({'query': 'LoRA'})`
  - `search_glossary({'query': 'QLoRA'})`

- 1つの質問でのLLM呼び出し回数：
  - 変更前：`requests=2`
  - 変更後：`requests=2`

- ツール呼び出し回数：
  - 変更前：`tool_calls=2`
  - 変更後：`tool_calls=2`

- 変更後の結果：
  - 指示を変更したが、search_glossaryは2回呼び出された。
  - LoRAとQLoRAの説明内容は用語集に基づいていた。
  - 今回はツール呼び出し回数に変化はなかった。

- 追加したツールと、docstringに書いた説明：
  - 追加なし（基礎課題では既存のツールを使用した）。

## 宿題

- 取り組んだレベル：基礎 
- やったこと：app/agent.py の INSTRUCTIONS にある、
「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する」
という指示を削除した。
- 結果：INSTRUCTIONSの指示を変更したが、今回の実行では
search_glossaryがLoRAとQLoRAについてそれぞれ1回ずつ呼ばれた。
変更前後でrequestsとtool_callsの数は変わらなかった。
- 気づき・疑問：保存が難しかった。
