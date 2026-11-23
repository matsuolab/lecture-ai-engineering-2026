# 第3回 解答

## 演習

第1回（素のLLM）とエージェントの回答の違い：素のLLMの場合は、Glossaryに記載がない部分も説明が行われ、エージェントはGlossaryに沿った回答を行った。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})

- 1つの質問での LLM 呼び出し回数（`requests`）：２回
- 追加したツールと、docstring に書いた説明：　
ツール　：　def make_quiz(lecture: int) -> str:
書いた説明
 """指定した回の用語から1つを選び、確認問題と答えを返す。
 「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
 """


## 宿題

- 取り組んだレベル：基礎
- やったこと：　agent.pyのInstructionから「必ず search_glossary で用語集を確認する」の行を消すと、検索せずに答えるようになるか　を検証した。
- 結果：該当の行を削除しても、検索は省略されていなかった。
- 気づき・疑問：
ツール定義（description）が呼び出しを誘導している：ツールの説明文や他の指示（「講座の用語集に基づく」など）が残っていれば、明示の行がなくても呼ぶ可能性がある。そのため、回数を重ねると参照しない回答があるかもしれない。
質問が用語集の語そのもの：「LoRAとQLoRA」は用語集の見出し語と一致するため、モデルが「検索すべき質問」と判断しやすい題材だったかもしれない。

- 取り組んだレベル：実装
- やったこと：　app/tools.py に save_learning_log を作り、def save_learning_log(title: str, content: str) -> str:　を作成した。
- 結果：
uv run python -m app.agent --trace "タイトルを「RAGの学習記録」にして、学んだ内容「ベクトル検索で関連文書を探す 」を学習記録として保存して"
[model] gemini-3.5-flash-lite

保存確認: save_learning_log
内容: {'title': 'RAGの学習記録', 'content': 'ベクトル検索で関連文書を探す'}
この学習記録を保存しますか？ [y/N]: N
学習記録の保存が拒否されました。この操作にはお客様の承認が必要です。保存をご希望の場合は、改めてご指示をお願いいたします。

--- trace ---
[tool call]   save_learning_log({'title': 'RAGの学習記録', 'content': 'ベクトル検索で関連文書を探す'})
[tool return] save_learning_log -> The tool call was denied.…
[usage] RunUsage(cost=Decimal('0.0002101'), details={'text_prompt_tokens': 467}, input_text_tokens=467, input_tokens=467, output_tokens=28, requests=1)

- 気づき・疑問：学習の記録を実装できることができたと思う。今後はAIとの会話から重要なキーワードと内容を記録させていく形になると思うので、活用したい。この記録も今後は自動化できると思うので今後の講義から学びたいと思う。