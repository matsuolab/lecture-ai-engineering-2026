# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
- 自分で学習を実行したか（`executed_training_myself`）：はい（実行できた範囲：　）
- 学習前：`format_rate` =　 / `content_rate` =　
- 学習後：`format_rate` =　 / `content_rate` =　
- 退行した質問：
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
- 学習で変わったこと・変わらなかったこと：

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ：`result.json` の `config` から：lorq-r を初期設定の16から8と20へ変更
- 結果（比較表や数字）：
- 初期設定１６
step	Training Loss
10	1.563429
20	0.084393
30	0.018156
40	0.01366
学習時間: 224 秒 | ステップ数: 40 | エポック: 20.0	

- ８へ変更
- step	Training Loss
- 10	1.556715
- 20	0.083699
- 30	0.016827
- 40	0.013121
- 学習時間: 224 秒 | ステップ数: 40 | エポック: 20.0	
- 学習時間に変化なし

- ２０へ変更
- step	Training Loss
- 10	1.56066
- 20	0.084343
- 30	0.018725
- 40	0.014068
- 学習時間: 247 秒 | ステップ数: 40 | エポック: 20.0	
-　学習時間が23秒増加

JSON提出
初期設定：lorq-r　16

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
  },
  "versions": {
    "transformers": "5.18.0",
    "peft": "0.21.1",
    "trl": "1.14.2",
    "torch": "2.11.0+cu130"
  },
  "method": "LoRA（量子化なし）",
  "before": {
    "label": "before",
    "n": 21,
    "format_rate": 0.09523809523809523,
    "content_rate": 0.0,
    "both_rate": 0.0,
    "seconds": 42.7
  },
  "after": {
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 45.9
  },
  "regressed": [],
  "knowledge": [
    {
      "質問": "この講座の最終課題の締切はいつですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"9 月 30 日 23:59\"}",
      "学習後の分類": "asserted",
      "学習後の出力": "{\"answer\": \"課題の提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}"
    },
    {
      "質問": "担当教員の名前は何ですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"確認が必要\"}",
      "学習後の分類": "needs_review",
      "学習後の出力": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}"
    },
    {
      "質問": "次回の講義のテーマは何ですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"次回の講義のテーマは「学習ポータル」の「課題」欄で提出する PDF 1 ファイルを提出します。\"}",
      "学習後の分類": "needs_review",
      "学習後の出力": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}"
    },
    {
      "質問": "課題の提出期限はいつですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"9 月 30 日 23:59\"}",
      "学習後の分類": "asserted",
      "学習後の出力": "{\"answer\": \"課題の提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}"
    }
  ],
  "executed_training_myself": true
}

設定変更１：lorq-r　16
{
  "config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 20,
    "warmup_steps": 6,
    "lr": 0.0002,
    "lora_r": 20,
    "lora_alpha": 32,
    "max_seq_len": 512,
    "max_new_tokens": 96,
    "gen": {
      "do_sample": false
    }
  },
  "versions": {
    "transformers": "5.18.0",
    "peft": "0.21.1",
    "trl": "1.14.2",
    "torch": "2.11.0+cu130"
  },
  "method": "LoRA（量子化なし）",
  "before": {
    "label": "before",
    "n": 21,
    "format_rate": 0.09523809523809523,
    "content_rate": 0.0,
    "both_rate": 0.0,
    "seconds": 28.2
  },
  "after": {
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 41.7
  },
  "regressed": [],
  "knowledge": [
    {
      "質問": "この講座の最終課題の締切はいつですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"9 月 30 日 23:59\"}",
      "学習後の分類": "asserted",
      "学習後の出力": "{\"answer\": \"課題の提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}"
    },
    {
      "質問": "担当教員の名前は何ですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"確認が必要\"}",
      "学習後の分類": "needs_review",
      "学習後の出力": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}"
    },
    {
      "質問": "次回の講義のテーマは何ですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"次回の講義のテーマは「学習ポータル」の「課題」欄で提出する PDF 1 ファイルを提出します。\"}",
      "学習後の分類": "needs_review",
      "学習後の出力": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}"
    },
    {
      "質問": "課題の提出期限はいつですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"9 月 30 日 23:59\"}",
      "学習後の分類": "asserted",
      "学習後の出力": "{\"answer\": \"課題の提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}"
    }
  ],
  "executed_training_myself": true

  設定変更１：lorq-r　20
{
  "config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 20,
    "warmup_steps": 6,
    "lr": 0.0002,
    "lora_r": 20,
    "lora_alpha": 32,
    "max_seq_len": 512,
    "max_new_tokens": 96,
    "gen": {
      "do_sample": false
    }
  },
  "versions": {
    "transformers": "5.18.0",
    "peft": "0.21.1",
    "trl": "1.14.2",
    "torch": "2.11.0+cu130"
  },
  "method": "LoRA（量子化なし）",
  "before": {
    "label": "before",
    "n": 21,
    "format_rate": 0.09523809523809523,
    "content_rate": 0.0,
    "both_rate": 0.0,
    "seconds": 28.2
  },
  "after": {
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 41.7
  },
  "regressed": [],
  "knowledge": [
    {
      "質問": "この講座の最終課題の締切はいつですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"9 月 30 日 23:59\"}",
      "学習後の分類": "asserted",
      "学習後の出力": "{\"answer\": \"課題の提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}"
    },
    {
      "質問": "担当教員の名前は何ですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"確認が必要\"}",
      "学習後の分類": "needs_review",
      "学習後の出力": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}"
    },
    {
      "質問": "次回の講義のテーマは何ですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"次回の講義のテーマは「学習ポータル」の「課題」欄で提出する PDF 1 ファイルを提出します。\"}",
      "学習後の分類": "needs_review",
      "学習後の出力": "{\"answer\": \"この FAQ には記載がありません。運営に確認が必要です。\", \"needs_review\": true}"
    },
    {
      "質問": "課題の提出期限はいつですか",
      "FAQ にある": false,
      "学習前の分類": "format_error",
      "学習前の出力": "{\"answer\": \"9 月 30 日 23:59\"}",
      "学習後の分類": "asserted",
      "学習後の出力": "{\"answer\": \"課題の提出期限は 9 月 30 日 23:59（日本時間）です。\", \"needs_review\": false}"
    }
  ],
  "executed_training_myself": true

- ファインチューニングが向く場面・向かない場面についての考察：
ファインチューニングは**「知識を追加する技術」ではなく、「モデルの振る舞いを最適化する技術」**として活用するのが適切である。
- ランクを大きくする場合
- メリット：複雑で自由度の高い表現が必要なとき
- デメリット：・過学習（Overfitting）のリスクが高まる
- ランクを小さくする場合
- メリット：限られたGPUメモリで軽量に実験したいとき
- デメリット：表現力が不足し、複雑なタスクに対応できない

　以上
