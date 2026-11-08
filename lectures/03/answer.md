# 第3回 解答

## 演習

-- 第1回（素のLLM）とエージェントの回答の違い：今回は直接比較できていないが、エージェントは用語集を検索し、LoRAとQLoRAの違いを説明できた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` の2回。
- 1つの質問でのLLM呼び出し回数（requests）：2回
- 追加したツールと、docstringに書いた説明：ツールの追加は未実施。

## 宿題

- - 取り組んだレベル：基礎

- やったこと：
  `app/agent.py` の `INSTRUCTIONS` から、回答前に必ず `search_glossary` で用語集を確認するという指示を削除した。同じ質問「LoRA と QLoRA の違いは？」を変更前後で `--trace` 付きで実行した。

- 結果：
  - 変更前：search_glossary 2回（LoRA、QLoRA）、requests=2
  - 変更後：search_glossary 2回（LoRA、QLoRA）、requests=2

  指示を削除しても検索回数と引数は変わらなかった。回答の表現には多少の違いがあったが、説明内容はほぼ同じだった。

- 気づき・疑問：
  検索を必須とする指示を削除しても検索が実行された点が興味深かった。ツールのdocstringにも検索を促す説明が残っていることや、モデル自身が検索を必要と判断したことが考えられる。INSTRUCTIONSとdocstringのどちらがツール選択に強く影響するのか、さらに調べてみたい。