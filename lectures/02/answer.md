# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
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
- 自分で学習を実行したか（`executed_training_myself`）：はい 
- 学習前：`format_rate` =　 0.09523809523809523 / `content_rate` =　 0.0
- 学習後：`format_rate` =　1.0 / `content_rate` =　0.9047619047619048
- 退行した質問：学習前に形式も内容も通っていたものはなかった。
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：質問の15と20の内容が失敗になっていた。
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
学習前の分類でformat_errorが学習後の分類でasserteとneeds_reviewに分かれた。
- 学習で変わったこと・変わらなかったこと：学習語の出力に全てneeds_review": falseがついた。

## 宿題

- 取り組んだレベル：基礎 
- 変えた設定やデータ：num_train_epochs:20→10に変更
- 結果（比較表や数字）：Colab での使用量上限に達したため、現在 GPU に接続できなかったため、結果はわからなかった。
- ファインチューニングが向く場面・向かない場面についての考察：上記の理由により考察できなかった。
