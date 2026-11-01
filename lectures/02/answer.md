# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：Qwen/Qwen3.5-0.8B
- 自分で学習を実行したか（`executed_training_myself`）：はい 実行できた範囲：num_train_epochsの値を変更　）
- 学習前：`format_rate` =　0.09523809523809523　/ `content_rate` =　0.0
- 学習後：`format_rate` =　1.0 / `content_rate` =　0.9047619047619048
- 退行した質問：
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
- 学習で変わったこと・変わらなかったこと：

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ：num_train_epochsを10回・5回を学習させた
- 結果（比較表や数字）：
||変更点|format_rate|content_rate|最終loss|学習時間|ファイル|
|--|--|--|--|--|--|--|
|学習前||0.09523809523809523|0.0|21|||
|学習後|講師|1.0|0.9047619047619048|2|228|[result.json](result.json)・[eval_after.json](eval_after.json)・[eval_before.json](eval_before.json)|
|学習後|num_train_epochs=10|1.0|0.8571428571428571|3|117|[result_2.json](result_2.json)・[eval_after_2.json](eval_after_2.json)・[eval_before_2.json](eval_before_2.json)|
|学習後|num_train_epochs=5|1.0|0.7619047619047619|5|58|[result_3.json](result_3.json)・[eval_after_3.json](eval_after_3.json)・[eval_before_3.json](eval_before_3.json)|

問21
||学習前|学習後(講師)|学習後(10)|学習後(5)|
||形式／内容|形式／内容|形式／内容|形式／内容|
|--|--|--|--|--|
|0|×/×|〇/〇|〇/〇|〇/〇|
|1|×/×|〇/〇|〇/〇|〇/〇|
|2|×/×|〇/〇|〇/〇|〇/〇|
|3|×/×|〇/〇|〇/〇|〇/〇|
|4|×/×|〇/〇|〇/〇|〇/〇|
|5|×/×|〇/〇|〇/〇|〇/〇|
|6|×/×|〇/〇|〇/×|〇/×|
|7|×/×|〇/〇|〇/〇|〇/〇|
|8|×/×|〇/〇|〇/〇|〇/〇|
|9|×/×|〇/〇|〇/〇|〇/〇|
|10|×/×|〇/〇|〇/〇|〇/×|
|11|×/×|〇/〇|〇/〇|〇/〇|
|12|×/×|〇/〇|〇/〇|〇/〇|
|13|×/×|〇/〇|〇/〇|〇/〇|
|14|×/×|〇/〇|〇/〇|〇/〇|
|15|×/×|〇/×|〇/〇|〇/〇|
|16|〇/×|〇/〇|〇/〇|〇/〇|
|17|×/×|〇/〇|〇/×|〇/×|
|18|×/×|〇/〇|〇/〇|〇/×|
|19|×/×|〇/〇|〇/×|〇/×|
|20|〇/×|〇/×|〇/〇|〇/〇|
|計|2/0|21/19|21/18|21/16|

知識を問う問題
||学習前|学習後(講師)||学習後(10)||学習後(5)||
||分類|分類|回答|分類|回答|分類|回答|
|--|--|--|--|--|--|--|--|
|0|format_error|asserted|false|asserted|false|asserted|false|
|1|format_error|needs_review|true|needs_review|true|needs_review|true|
|2|format_error|needs_review|true|needs_review|true|needs_review|true|
|3|format_error|asserted|false|asserted|false|asserted|false|

- ファインチューニングが向く場面・向かない場面についての考察：
解答形式については、num_train_epochsを回数を小さくしても、学習が可能だったことが分かった。
少ない回数でも、解答形式については、進展がみられると考えらる。
逆に、知識を問う問題では、回数に対する変化が全く見られなかった。
このため、追加の知識を習得していないとの見方が可能である。
