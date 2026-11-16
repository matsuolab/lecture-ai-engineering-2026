# 第2回 解答

## 演習

Source: `lectures/02/result_epoch20.json` (default settings, run on Colab).

- 使ったモデル・設定（`result.json` の `config` から）：`Qwen/Qwen3.5-0.8B`, LoRA without quantization, `num_train_epochs` 20, `lr` 2e-4, `lora_r` 16, `lora_alpha` 32, `warmup_steps` 6, `seed` 42, greedy decoding (`do_sample: false`)
- 自分で学習を実行したか（`executed_training_myself`）：はい（`true`）
- 学習前：`format_rate` = 0.095 / `content_rate` = 0.00
- 学習後：`format_rate` = 1.00 / `content_rate` = 0.905 (19/21)
- 退行した質問：none (`regressed` is empty)
- 学習後に残った失敗と、その型：2 of 21 test questions still failed on content while keeping the correct format. `result.json` records only the rates, not which questions failed, so I can't name them from my saved results.
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
  - Final assignment deadline (not in FAQ): format_error → **asserted** ("9月30日 23:59", copied from the regular deadline FAQ item)
  - Instructor's name (not in FAQ): format_error → needs_review
  - Next lecture's theme (not in FAQ): format_error → needs_review
  - Assignment deadline (in FAQ, control): format_error → asserted (correct)
  - The model learned to say "not in the FAQ" for unrelated questions, but a question *close to* an FAQ item (final deadline vs. regular deadline) still got a confident wrong answer.
- 学習で変わったこと・変わらなかったこと：The output format changed completely (JSON with `answer` + `needs_review`, 9.5% → 100%). Judging whether the FAQ actually supports an answer improved but did not become reliable: near-topic questions are still asserted.

## 宿題

### Level
Basic

### What I changed
num_train_epochs: 20 → 5. All other settings kept the same
(Qwen/Qwen3.5-0.8B, lr 2e-4, lora_r 16, lora_alpha 32, warmup_steps 6, seed 42, greedy decoding).
I restarted the session and ran from the top for each run.

### Results

| | 20 epochs | 5 epochs |
|---|---:|---:|
| Steps | 40 | 10 |
| format_rate (before → after) | 0.095 → 1.00 | 0.095 → 1.00 |
| content_rate (before → after) | 0.00 → 0.905 (19/21) | 0.00 → 0.762 (16/21) |
| Logged loss at step 10 | 1.558 | 1.577 |
| Final logged loss | 0.014 (step 40) | 1.577 (step 10) |
| Training time | 230 s | 54 s |
| Regressed questions | none | none |
| Knowledge questions (after) | 2 needs_review, 2 asserted | 2 needs_review, 2 asserted |

The "before" results were identical in both runs, so the comparison is fair.

### Observations
- **Format was learned with only 10 steps.** Both runs reached 100% format compliance.
- **Content needed more training.** With 5 epochs, content_rate dropped by 3 questions.
  The "needs review" answers came out in shortened forms
  ("FAQ には記載がありません。" instead of the trained phrase
  "この FAQ には記載がありません。運営に確認が必要です。"),
  so the wording was less exact.
- **The logged loss is an average.** The loss is logged every 10 steps as the mean of
  those steps, so the 5-epoch run's only value (1.577) mostly reflects the start of training.
  The model had clearly improved by step 10 (format 100%), but the loss number couldn't show it.
  Evaluating real outputs was necessary.
- **Warmup effect.** With 5 epochs, 6 of the 10 steps were warmup, so the model got even less
  effective training than "1/4 of the epochs" suggests.
- **Judgment did not change.** In both runs, the model asserted "9月30日 23:59" for the
  final assignment deadline, which is not in the FAQ. 4× more training did not fix this.
  (The 4th knowledge question, the regular assignment deadline, is the control and is in the FAQ,
  so "asserted" is correct there.)

### When fine-tuning fits and when it doesn't
- **Fits:** fixing an output format or style. Here, 10 steps were enough for 100% JSON compliance.
- **Doesn't fit (on its own):** teaching the model to recognize what it doesn't know.
  The unfounded assertion survived 4× more training. Checking the FAQ explicitly,
  for example with a search system, would handle this better.
- **Trade-off:** more epochs improved exact wording, but with only 14 training examples,
  this is mostly memorizing the training text rather than better understanding.

### Limitations
One run per setting. GPU training is not fully reproducible, so a 3-question difference
is suggestive, not conclusive.