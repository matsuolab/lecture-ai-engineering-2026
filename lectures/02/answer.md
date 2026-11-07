# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
"config": {
  "base_model": "Qwen/Qwen3.5-0.8B",
  "revision": "2fc06364715b967f1860aea9cf38778875588b17",
  "seed": 42,
  "num_train_epochs": 20,
  "warmup_steps": 6,
  "lr": 0.0002,
  "lora_r": 16,
  "lora_alpha": 32,
  "max_seq_len": 512,
  "max_new_tokens": 96,
  "gen": {
    "do_sample": false
  }
- 自分で学習を実行したか（`executed_training_myself`）：はい
- 学習前：`format_rate` =　0.09523809523809523 / `content_rate` =　0.0
- 学習後：`format_rate` =　1.0 / `content_rate` =　0.9047619047619048
- 退行した質問：PDF以外でもだせますか、成績はいつ出ますか
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：根拠なしの質問に断定した
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：学習前は全て"format_error"となっていたが、学習後は"asserted"または"needs_review"に分類されていた。
- 学習で変わったこと・変わらなかったこと：学習後では設定された形式で出力されていた。教師データ文に近しい内容の質問だと間違った回答をしていた。

## 宿題

- 取り組んだレベル：基礎 
- 変えた設定やデータ：lr 2e-4→1e-2
- 結果（比較表や数字）：値が大きすぎたことによってモデルが壊れた
学習結果
Step	Training Loss
10	10.997493
20	18.218336
30	9.764365
40	7.534363
学習時間: 236 秒 | ステップ数: 40 | エポック: 20.0

label					
before	21	0.095238	0.000000	0.000000	22.7
before_4bit	21	0.666667	0.333333	0.333333	43.6

質問	正解の needs_review	4bit・学習前の出力	形式/内容	形式の失敗理由
0	提出の期限は？	False	{"answer": "9 月 30 日 23:59（日本時間）", "needs_review": false}	○/○	
1	提出期限の日付と時刻を教えてください	False	{"answer": "9 月 30 日 23:59", "needs_review": false}	○/○	
2	課題の締切は何月何日の何時ですか	False	{"answer": "9 月 30 日 23:59", "needs_review": false}	○/○	
3	提出場所は？	False	{"answer": "学習ポータルの「課題」欄", "needs_review": false}	○/○	
4	課題の提出はどこで行いますか	False	{"answer": "学習ポータルの「課題」欄で提出先を指定し、提出形式は PDF 1 ファイル（学籍番号_課題番号.pdf）で、提出時間は毎週火曜 17:00〜18:00 のオフィスアワーで受け付けます。"}	×/×	missing_key
5	提出物を出す先を教えてください	False	{"answer": "学習ポータルの「課題」欄で提出先を指定してください。提出形式は PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です。提出後、期限から 48 時間以内なら減点のうえ受け付けます。"}	×/×	missing_key
6	PDF 以外でも出せますか	False	{"answer": "確認が必要"}	×/×	missing_key
7	提出するファイルの形式は何ですか	False	{"answer": "PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です"}	×/×	missing_key
8	提出ファイルは何形式で、いくつ出しますか	False	{"answer": "PDF 1 ファイルで、1 出します", "needs_review": false}	○/○	
9	相談できる時間帯は？	False	{"answer": "17:00〜18:00", "needs_review": false}	○/×	
10	オフィスアワーの曜日と時間を教えてください	False	{"answer": "火曜 17:00〜18:00", "needs_review": false}	○/○	
11	質問を受け付けてもらえるのは何曜日の何時からですか	False	{"answer": "火曜 17:00〜18:00", "needs_review": false}	○/○	
12	締切後の扱いを教えてください	False	{"answer": "確認が必要", "needs_review": true}	○/×	
13	提出が締切に間に合わなかったらどうなりますか	False	{"answer": "提出が締切に間に合わなかったら、期限から 48 時間以内なら減点のうえ受け付けます。"}	×/×	missing_key
14	期限後に提出した課題は受理されますか	False	{"answer": "確認が必要", "needs_review": true}	○/×	
15	成績はいつ出ますか	True	{"answer": "確認が必要"}	×/×	missing_key
16	講義の録画は公開されますか	True	{"answer": "なし", "needs_review": false}	○/×	
17	課題の文字数に制限はありますか	True	{"answer": "なし", "needs_review": "false"}	×/×	wrong_type
18	提出した課題へのフィードバックはもらえますか	True	{"answer": "はい", "needs_review": false}	○/×	
19	参考文献の書き方に指定はありますか	True	{"answer": "なし", "needs_review": false}	○/×	
20	オフィスアワーは事前予約が必要ですか	True	{"answer": "はい", "needs_review": false}	○/×	
- 変えた設定やデータ：lr 2e-4→5e-5
- 結果（比較表や数字）：2e-4よりも回答の精度が上がった
学習結果
Step	Training Loss
10	2.135941
20	0.929047
30	0.297995
40	0.150533
学習時間: 223 秒 | ステップ数: 40 | エポック: 20.0

label					
before	21	0.095238	0.000000	0.000000	21.6
after	21	1.000000	0.857143	0.857143	47.6


退行: []
質問	正解の needs_review	学習前の出力	学習前 形式/内容	学習後の出力	学習後 形式/内容
0	提出の期限は？	False	{"answer": "9 月 30 日 23:59"}	×/×	{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}	○/○
1	提出期限の日付と時刻を教えてください	False	{"answer": "9 月 30 日 23:59"}	×/×	{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}	○/○
2	課題の締切は何月何日の何時ですか	False	{"answer": "9 月 30 日 23:59"}	×/×	{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}	○/○
3	提出場所は？	False	{"answer": "学習ポータルの「課題」欄"}	×/×	{"answer": "提出先は学習ポータルの「課題」欄です。", "needs_review": false}	○/○
4	課題の提出はどこで行いますか	False	{"answer": "学習ポータルの「課題」欄で提出先を指定し、PDF 1 ファイルで提出します。提出時間は毎週火曜 17:00〜18:00 のオフィスアワーで行います。"}	×/×	{"answer": "提出先は学習ポータルの「課題」欄です。", "needs_review": false}	○/○
5	提出物を出す先を教えてください	False	{"answer": "学習ポータルの「課題」欄"}	×/×	{"answer": "提出先は学習ポータルの「課題」欄です。", "needs_review": false}	○/○
6	PDF 以外でも出せますか	False	{"answer": "確認が必要"}	×/×	{"answer": "FAQ には記載がありません。提出先は学習ポータルの「課題」欄です。", "needs_review": true}	○/×
7	提出するファイルの形式は何ですか	False	{"answer": "PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です"}	×/×	{"answer": "提出形式は PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です。", "needs_review": false}	○/○
8	提出ファイルは何形式で、いくつ出しますか	False	{"answer": "PDF 1 ファイルで、1 出します"}	×/×	{"answer": "提出形式は PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です。", "needs_review": false}	○/○
9	相談できる時間帯は？	False	{"answer": "火曜 17:00〜18:00 のオフィスアワー"}	×/×	{"answer": "質問は毎週火曜 17:00〜18:00 のオフィスアワーで受け付けます。", "needs_review": false}	○/○
10	オフィスアワーの曜日と時間を教えてください	False	{"answer": "火曜 17:00〜18:00"}	×/×	{"answer": "質問は毎週火曜 17:00〜18:00 のオフィスアワーで受け付けます。", "needs_review": false}	○/○
11	質問を受け付けてもらえるのは何曜日の何時からですか	False	{"answer": "火曜 17:00〜18:00"}	×/×	{"answer": "質問は毎週火曜 17:00〜18:00 のオフィスアワーで受け付けます。", "needs_review": false}	○/○
12	締切後の扱いを教えてください	False	{"answer": "期限後 48 時間以内なら減点のうえ受け付けます。"}	×/×	{"answer": "期限後の提出は、期限から 48 時間以内なら減点のうえ受け付けます。", "needs_review": false}	○/○
13	提出が締切に間に合わなかったらどうなりますか	False	{"answer": "期限から 48 時間以内なら減点のうえ受け付けます"}	×/×	{"answer": "期限後の提出は、期限から 48 時間以内なら減点のうえ受け付けます。", "needs_review": false}	○/○
14	期限後に提出した課題は受理されますか	False	{"answer": "確認が必要"}	×/×	{"answer": "期限後の提出は、期限から 48 時間以内なら減点のうえ受け付けます。", "needs_review": false}	○/○
15	成績はいつ出ますか	True	{"answer": "確認が必要"}	×/×	{"answer": "質問は FAQ に記載がありません。確認が必要です。", "needs_review": true}	○/○
16	講義の録画は公開されますか	True	{"answer": "否", "needs_review": false}	○/×	{"answer": " FAQ に記載がありません。確認が必要です。", "needs_review": true}	○/○
17	課題の文字数に制限はありますか	True	{"answer": "なし"}	×/×	{"answer": "課題の文字数に制限はありますか。 FAQ に記載がありません。", "needs_review": true}	○/×
18	提出した課題へのフィードバックはもらえますか	True	{"answer": "確認が必要"}	×/×	{"answer": " FAQ に記載がありません。確認が必要です。", "needs_review": true}	○/○
19	参考文献の書き方に指定はありますか	True	{"answer": "確認が必要"}	×/×	{"answer": "参考文献の書き方に指定は記載がありません。", "needs_review": true}	○/×
20	オフィスアワーは事前予約が必要ですか	True	{"answer": "否", "needs_review": false}	○/×	{"answer": " FAQ には記載がありません。必ず確認が必要です。", "needs_review": true}	○/○

- ファインチューニングが向く場面・向かない場面についての考察：今回の学習結果から大規模で多様な学習サンプルデータがある場合、閉域な環境で独自の規則等がある場合はファインチューニングに向く、しかしサンプルデータが少なく偏ったサンプルデータの場合、汎用的な質問だけしか扱わずベースモデルで対応可能な場合は向かないと考察される。
