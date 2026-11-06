# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：
- 1つの質問での LLM 呼び出し回数（`requests`）：
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：基礎
- やったこと：INSTRUCTIONSの内容を変更.変更後は、複数の関連用語をqueryにまとめて検索するように指示した。
- 結果：まとめて検索する場合は、

[tool call] search_glossary({'query': 'LoRA QLoRA'})

となり、tool_callsは1回だった。

一方、用語ごとに検索する場合は、

[tool call] search_glossary({'query': 'LoRA'})
[tool call] search_glossary({'query': 'QLoRA'})

となり、tool_callsは2回だった。

- 気づき・疑問：requestsはいずれも2であり、
ツールの呼び出し回数は変わったが、
LLMを呼び出した回数は変わらなかった。

output_tokensは実行ごとに変化したが、
LLMの回答表現の揺らぎも含まれるため、
tool_callsの変更だけが原因とは断定できない。