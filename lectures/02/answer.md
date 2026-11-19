# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
  "base_model": "Qwen/Qwen3.5-0.8B",
  "revision": "2fc06364715b967f1860aea9cf38778875588b17",
  "seed": 42,
  "num_train_epochs": 10,
  "warmup_steps": 6,
  "lr": 0.0002,
  "lora_r": 16,
  "lora_alpha": 32,
  "max_seq_len": 512,
  "max_new_tokens": 96,
- 自分で学習を実行したか（`executed_training_myself`）：はい
- 学習前：`format_rate` =　0.09523809523809523 / `content_rate` =　0.0
- 学習後：`format_rate` =　1.000000 / `content_rate` =　0.761905
- 退行した質問：なし
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
根拠なしの質問に断定した　3件 / 根拠ありの質問に確認要求で逃げた　2件
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：FAQにあるが１件目が正しく分類されなかった。また、format_errorが正しく出力された。
- 学習で変わったこと・変わらなかったこと：フォーマットの出力は正しくなるが、内容の正しさはバラツキがある。

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ："num_train_epochs": 5　,　"num_train_epochs": 10
- 結果（比較表や数字）：

＃"num_train_epochs": 5の結果
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.7619047619047619,
    "both_rate": 0.7619047619047619,
    "seconds": 47.6

＃"num_train_epochs": 10の結果
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.8571428571428571,
    "both_rate": 0.8571428571428571,
    "seconds": 42.7

- ファインチューニングが向く場面・向かない場面についての考察：
　-フォーマットの修正は優れているが内容修正は向いていない。
　-epoch数を増やすとcontent_rateとboth_rateが向上することがわかった。
