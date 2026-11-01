# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
  base_model：Qwen/Qwen3.5-0.8B
  Lora設定：r=16、lora_alpha = 32
  lr：0.0002
  num_train_epochs：20
  seed：42
- 自分で学習を実行したか（`executed_training_myself`）：はい
- 学習前：`format_rate` =　0.095238 / `content_rate` =　0.000000
- 学習後：`format_rate` =　1.000000 / `content_rate` =　0.904762
- 退行した質問：なし
- 学習後に残った失敗と、その型：21問中2問で不正解が発生した。（根拠なしの質問に断定した）
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：ファインチューニングをしても、「FAQに根拠があるかどうかを正しく判断して回答を出し分ける能力」までは完璧には身に付かないことがわかった。
- 学習で変わったこと・変わらなかったこと：回答パターンを習得した点は変わった。FAQに書いていないことについては誤りの回答を出力する傾向が引き続き見られた。

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ：num_train_epochs を20から50に増やした。

- 結果（比較表や数字）：

&nbsp;&nbsp;【変更前（num_train_epochs=20）】<br>
&nbsp;&nbsp;format_rate：1.000000<br>
&nbsp;&nbsp;content_rate：0.904762<br>
&nbsp;&nbsp;最終 loss：0.014056<br>
&nbsp;&nbsp;学習時間：238 秒

&nbsp;&nbsp;【変更後（num_train_epochs=50）】<br>
&nbsp;&nbsp;format_rate：1.000000<br>
&nbsp;&nbsp;content_rate：0.857143<br>
&nbsp;&nbsp;最終 loss：0.010768<br>
&nbsp;&nbsp;学習時間：626 秒

- ファインチューニングが向く場面・向かない場面についての考察：<br>
&nbsp;&nbsp;向く場面については、「どう答えるか（形式・トーン・構造）」や<br>
&nbsp;&nbsp;「手元にある明確なルールに準拠するような定型回答」についての学習の場面が該当すると考えられる。<br>
&nbsp;&nbsp;一方で、向かない場面については、「未知の知識や変動する外部データ」の学習の場面や、<br>
&nbsp;&nbsp;柔軟な回答が必要な中で過学習による正解率の低下が起きてしまうような場面が該当すると考えられる。
