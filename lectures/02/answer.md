# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
- 自分で学習を実行したか（`executed_training_myself`）：はい / いいえ（実行できた範囲：　）
- 学習前：`format_rate` =　 / `content_rate` =　
- 学習後：`format_rate` =　 / `content_rate` =　
- 退行した質問：
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
- 学習で変わったこと・変わらなかったこと：

## 宿題

- 取り組んだレベル：基礎 
- 変えた設定やデータ：lr(学習率)をもともとの 2e-4 から 1e-4 に変更しました
- 結果（比較表や数字）：
　変更前と変更後のresult.jsonやeval_after.jsonで差異があった部分は以下の通りです。

  「変更前のresult.json」
    "method": "LoRA（量子化なし）",
  "before": {
    "label": "before",
    "n": 21,
    "format_rate": 0.09523809523809523,
    "content_rate": 0.0,
    "both_rate": 0.0,
    "seconds": 21.6
  },
  "after": {
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 42.5
  },

  「変更後のresult.json」
  "method": "LoRA（量子化なし）",
  "before": {
    "label": "before",
    "n": 21,
    "format_rate": 0.09523809523809523,
    "content_rate": 0.0,
    "both_rate": 0.0,
    "seconds": 29.9
  },
  "after": {
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 40.7
  },

  「変更前のeval_after.json」
    {
      "question": "PDF 以外でも出せますか",
      "raw": "{\"answer\": \"提出形式は PDF 1 ファイルで、ファイル名は 学籍番号_課題番号.pdf です。\", \"needs_review\": false}",
      "format_ok": true,
      "format_reason": "",
      "content_ok": true,
      "both_ok": true,
      "gold_needs_review": false
    },
    {
      "question": "成績はいつ出ますか",
      "raw": "{\"answer\": \"提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}",
      "format_ok": true,
      "format_reason": "",
      "content_ok": false,
      "both_ok": false,
      "gold_needs_review": true
    },

  「変更後のeval_after.json」
    {
      "question": "PDF 以外でも出せますか",
      "raw": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}",
      "format_ok": true,
      "format_reason": "",
      "content_ok": false,
      "both_ok": false,
      "gold_needs_review": false
    },
    {
      "question": "成績はいつ出ますか",
      "raw": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}",
      "format_ok": true,
      "format_reason": "",
      "content_ok": true,
      "both_ok": true,
      "gold_needs_review": true
    },

- ファインチューニングが向く場面・向かない場面についての考察：
  -  ファインチューニングは「知識の注入」ではなく「振る舞いの調整」に向くと考えます。
  -  具体的には、応答のスタイルやトーン、構造化出力（JSON等の決まったフォーマット）、ドメイン特有のパターン、
     文脈不足時の拒否挙動など、安定していて変化しにくい要素の最適化に適します。
  -  モデルが事前学習で既に理解しているタスク（例：SQL構文）をさらに洗練させる用途も向いているものと思われます。
  -  一方、頻繁に変わる最新知識や固有の事実をモデルに覚えさせる用途には不向きではないかと考えます。
  -  こうしたケースでは、RAGを使うほうがよいのかなと感じています。
  -  また、全く新しい言語の生成などモデルが未知のタスクは、ゼロから学習が必要となり、既存知識との衝突でハルシネーションを招くため不向きと考えます。