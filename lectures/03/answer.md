# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：tool callで呼び出した結果を元に答えた。
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary({'query': 'LoRA'})

[tool call]   search_glossary({'query': 'LoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[usage] RunUsage(cost=Decimal('0.0007085'), details={'text_prompt_tokens': 1095}, input_text_tokens=1095, input_tokens=1095, output_tokens=152, requests=2, tool_calls=1)

- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：
def make_quiz(lecture: int) -> str:
    """指定した回の用語から 1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """

## 宿題

- 取り組んだレベル：基礎
- やったこと：agent.pyのINSTRUCTIONS の末尾に以下を加えた。
  用語を元にクイズを1問作って、解答と解説を付ける。クイズは「選択肢4つの4択問題」にする。
- 結果：変更前の結果に、模擬試験問題の出力が追加された。
詳細はbefore.txtとafter.txtにある。
- 気づき・疑問：INSTRUCTIONSの回答の最後に、関係する回（第N回）を示す。の内容が変わってしまった。
おそらくは、作成した模擬試験の内容が第3回だったのでそれに合わせたと思われる。

before
関連する回：第1回、第3回
after
（関連する回：第3回）

以上

