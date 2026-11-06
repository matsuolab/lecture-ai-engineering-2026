# 第3回 解答

## 演習

### 1. 第1回（素のLLM）とエージェントの回答の違い

質問：AIE2026の講座の宿題にある「3レベル」とは何ですか？

| 観点 | 第1回 app.ask（素のLLM） | 第3回 app.agent |
|---|---|---|
| 答え方 | 「〜と推測します」と前置きし、一般論を回答 | search_glossary で用語集を確認してから回答 |
| レベルの名前 | レベル1〜3（基礎・応用・発展） | 基礎・実装・発展（用語集の定義と一致） |
| 完了条件 | 「全員レベル1は必須」など本講座に無いルールを補った | どれか1つで完了、原則採点なし |
| 根拠 | 「必ず記載されているはず」と断定 | 末尾に「（関連：第1回）」 |
| 出力トークン | 492 | 短い |

素のLLMは知らないことを一般論で埋めて断定する。エージェントは答える前に用語集を検索し、定義に基づいて答える。

### 2. --trace で見えたツール呼び出し（ツール名と引数）

質問「LoRAとQLoRAの違いは？」
- search_glossary({'query': 'LoRA'})
- search_glossary({'query': 'QLoRA'})

docstring の「query には用語を1つだけ入れる」に従い、1語ずつ別々に検索された。

質問「第2回の内容から確認問題を1問出して」
- make_quiz({'lecture': 2})

「第2回」から lecture=2 を選んだ。戻り値に answer も含まれていたが、モデルは問題文だけを出し、答えは伏せた。

### 3. 1つの質問での LLM の呼び出し回数（requests）

| 質問 | requests | tool_calls | input_tokens |
|---|---|---|---|
| LoRAとQLoRAの違いは？ | 2 | 2 | 1196 |
| 第2回の確認問題を1問出して | 2 | 1 | 896 |

1回目でツール呼び出しを決め、2回目で結果を受けて回答する。2つの検索は1回の応答で同時に依頼されたため、requests は3ではなく2だった。input_tokens はツールの戻り値を含むため、検索結果2件分の1問目の方が多い。

### 4. 追加したツールと、docstring に書いた説明

app/tools.py に make_quiz(lecture: int) -> str を追加し、app/agent.py で agent.tool_plain(tools.make_quiz) として登録した。

docstring：

    指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    lecture には回の番号（1始まりの整数）を入れる。

- load_glossary() から lecture が一致する用語を集め、random.choice で1つ選び、question・answer・lecture を json.dumps で返す
- 用語が無い回（lecture=0 など）は例外を出さず案内文を返す
- --list-tools で make_quiz と docstring が表示され、--trace で呼ばれ、pytest は11件 passed（--ignore=tests/test_ask.py）

### 気づき・疑問

- --list-tools の説明文は docstring そのもので、モデルはこれを読んでツールを選ぶ
- 第1回で app/ask.py に応答時間・トークン数の表示を足していたため、tests/test_ask.py の1件が出力順の違いで失敗した。追加したツールとは無関係だが、自分の改造が講座のテストとずれることがあると分かった

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
