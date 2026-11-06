# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：
- 1つの質問での LLM 呼び出し回数（`requests`）：
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：基礎
- やったこと：
  同じ質問「LoRA とQLoRAの違いは？」を `--trace` 付きで実行し、次の2か所を1か所ずつ変えて比較した。
  1. `app/agent.py` の INSTRUCTIONS から「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。」の行を削除
  2. `app/tools.py` の `search_glossary` の docstring を「query には調べたい用語を1つだけ入れる」→「調べたい用語をまとめて入れる」に変更
- 結果：

  | 条件 | tool call（引数） | tool_calls | requests | 回答 |
  |---|---|---|---|---|
  | 変更前 | search_glossary('LoRA'), search_glossary('QLoRA') | 2 | 2 | LoRA/QLoRA 両方を用語集の定義で説明。最後に第2回を示す |
  | ① INSTRUCTIONS の行を削除 | search_glossary('LoRA'), search_glossary('QLoRA') | 2 | 2 | 変更前とほぼ同じ。「必ず確認する」が無くても検索した |
  | ② docstring を「まとめて入れる」に変更 | search_glossary('LoRA QLoRA') | 1 | 2 | 用語集から返ったのは LoRA の定義のみだったが、回答には QLoRA の説明も含まれた |

- 気づき・疑問：
  - 「必ず search_glossary で確認する」の指示を消しても、ツールの docstring（「答える前に使うこと」）だけでモデルは検索を選んだ。INSTRUCTIONS と docstring は重複して効いている。
  - docstring の1文を変えるだけで、モデルが渡す引数が変わり、呼び出し回数が半分になった。ツールの説明文はコストと挙動を直接左右する。
  - まとめ検索では用語集が片方（LoRA）しか返さなかったのに、回答には QLoRA の説明があった。これはモデル自身の知識で補った可能性があり、「用語集にないことは推測しない」という指示と矛盾しかねない。docstring が「1つだけ」としていたのは、用語集の検索精度を保つためだと理解した。
  - 疑問：同じ条件でも実行ごとに呼び出し回数が変わることはあるのか（確率的なゆらぎ）。複数回走らせて確認したい。