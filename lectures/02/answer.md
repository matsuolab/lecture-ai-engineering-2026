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
  }
- 自分で学習を実行したか（`executed_training_myself`）：はい（実行できた範囲：　セクション1~7）
- 学習前：`format_rate` =　0.09523809523809523 / `content_rate` =　0.0
- 学習後：`format_rate` =　1.0/ `content_rate` =　0.9047619047619048
- 退行した質問：なし
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：根拠無しの質問に断定した(asserted)
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：学習前はformat_errorしか分類が存在しなかったが、学習後はその分類がassertedとneeds_reviewとなった。
- 学習で変わったこと・変わらなかったこと：学習させた知識に対して、学習前とくらべて大幅に精度よく型通りに回答ができるようになった。しかし、根拠がないのに断定する性質はそのままの質問も存在した。

## 宿題

- 取り組んだレベル：基礎
- 変えた設定やデータ：lrを2e-4 → 2e-1 に変更した。
- 結果（比較表や数字）：
{
  "config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 20,
    "warmup_steps": 6,
    "lr": 0.2,
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
    "seconds": 39.8
  },
  "after": {
    "label": "after",
    "n": 21,
    "format_rate": 0.0,
    "content_rate": 0.0,
    "both_rate": 0.0,
    "seconds": 128.5
  },
  "regressed": [],
  "executed_training_myself": true
}

学習率を大幅に大きくした結果、かえってスコアは低くなってしまった。間違いの仕方何も回答せずにformat_errorとなっているので、学習率の適切な調整が必要だと感じた。

- ファインチューニングが向く場面・向かない場面についての考察：講座の内容に関する質問のような特定の分野・フォーマットのために一般モデルをファインチューニングすることは価値があると感じた。反対に、多くバックグラウンドを持つ人が使用するモデルに対してファインチューニングすることは向いていないと考える。
