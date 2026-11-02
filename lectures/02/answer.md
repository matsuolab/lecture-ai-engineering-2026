# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：Qwen/Qwen3.5-0.8B
- 自分で学習を実行したか（`executed_training_myself`）：はい
- 学習前：`format_rate` =0.095　 / `content_rate` =　0.0
- 学習後：`format_rate` =1.0　 / `content_rate` =　0.857
- 退行した質問：なし（型を全て正しく答えた。学習前の内容の正答率が0だった。）
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
不正解のものはいずれもneeds_reviewの要素がなかった。いずれもgold_needs_review「人間による確認が必要」の要素が必要だった。
>    {
>      "question": "成績はいつ出ますか",
>      "raw": "{\"answer\": \"提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}",
>      "format_ok": true,
>      "format_reason": "",
>      "content_ok": false,
>      "both_ok": false,
>      "gold_needs_review": true
>    },<br>
>{
>      "question": "課題の文字数に制限はありますか",
>      "raw": "{\"answer\": \"提出形式は PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です。\", \"needs_review\": false}",
>      "format_ok": true,
>      "format_reason": "",
>      "content_ok": false,
>      "both_ok": false,
>      "gold_needs_review": true
>    },<br>
>{
>      "question": "オフィスアワーは事前予約が必要ですか",
>      "raw": "{\"answer\": \"質問は毎週火曜 17:00〜18:00 のオフィスアワーで受け付けます。\", \"needs_review\": false}",
>      "format_ok": true,
>      "format_reason": "",
>      "content_ok": false,
>      "both_ok": false,
>      "gold_needs_review": true
>    }
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
型の学習は非常によくできるが、未知の質問に関してはすぐにあきらめたりせず、似た知識（FAQ）を引っ張ってきて強引に断定しようとする傾向がある。
- 学習で変わったこと・変わらなかったこと：LoRA学習後は100%正しくJSON構造を出力できるようになった。未知の質問に対しては断定して既知の回答を割り当ててしまう傾向は変わらなかった。

## 宿題

- 取り組んだレベル：基礎 
- 変えた設定やデータ：num_train_epochs を 20 から 5 に変更して比較検証を行った。
- 結果（比較表や数字）：学習時間は 238秒 から 59秒 へと約 1/4 （エポック数の比）に短縮された。内容正解率（content_rate）は 0.7619 (18/21→16/21) となり、元設定より低下したものの、未知の質問で確認が必要なものについて元設定のときに間違えていたものを正解したものがあった。

- ファインチューニングが向く場面・向かない場面についての考察：
gold_needs_review: false（既知FAQ）の質問で不正解が発生したことから、エポック数5ではFAQデータの知識や必須キーワードを定着させるための学習量が不十分（未学習 / Underfitting）であったことが確認できた。
一方で、エポック数20の時点で発生していた「類似キーワードへの過剰反応による誤断定（asserted）」がエポック数5では抑制され、一部の未知質問で正解（needs_review: true）を出せるようになるという過学習（Overfitting）の緩和現象も観察された。
したがって、エポック数は「既知情報の記憶」と「未知情報に対する過学習防止」のバランスを考慮して適切に設定する必要がある。
