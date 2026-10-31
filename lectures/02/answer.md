# 第2回 解答

## 演習

- 使ったモデル・設定（`config` から）：lora r16 -> lora r8
- 自分で学習を実行したか（`executed_training_myself`）：はい 実行できた範囲：　）
- 学習前：`format_rate` = 0.09523809523809523　 / `content_rate` =　0.0
- 学習後：`format_rate` =　0.9047619047619048 / `content_rate` =　0.9047619047619048

## 宿題

- 取り組んだレベル：基礎 
- 変えた設定やデータ：lora r16 -> lora _r8
- 結果（比較表や数字）：result.jsonの比較
- lora r16 after
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 65.0
- lora r8 after
    "format_rate": 1.0,
    "content_rate": 0.9523809523809523,
    "both_rate": 0.9523809523809523,
    "seconds": 48.2
- ファインチューニングが向く場面・向かない場面についての考察：lora を16bit から 8bitに変えても学習は改善し、計算時間も65sec から 48.2に改善
