# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：{
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
  },
  "work_dir": "/content/qlora_lab",
  "drive_dir": "/content/drive/MyDrive/aie2026/qlora_lab"
}
- 自分で学習を実行したか（`executed_training_myself`）：false （実行できた範囲：　）
- 学習前：`format_rate` =0.09523809523809523 / `content_rate` =　0
- 学習後：`format_rate` =　1/ `content_rate` =　0.9047619047619048
- 退行した質問：なし
- 学習後に残った失敗と、その型（needs_reviwがtrueのものをfalseにして変えした。）：
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：間違った部分が、変わっていないが、嘘をつかなくなった。
- 学習で変わったこと・変わらなかったこと：formatを合わせるようになった。

## 宿題

- 取り組んだレベル：基礎 
- 変えた設定やデータ：num_train_epochs 20→5
- 結果（比較表や数字）：変更前　学習時間240 秒　format_rate` =　1/ `content_rate` =　0.9047619047619048
-                     変身後  学習時間56 秒　format_rate` =　1/ `content_rate` =　num_train_epochs
- result比較 　うそをでっちあげることもあったが、回答方法が正しくなったものもあった。
- ファインチューニングが向く場面・向かない場面についての考察：
- 向く場面　回答方法や形式の変身
- 向かない場面　新しい知識を得ること
- 
