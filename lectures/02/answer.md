# 第2回 解答 (Lecture 2 Answers)

## 演習 (Exercise)

- Model and settings (from `config` in `result.json`): Qwen/Qwen3.5-0.8B, LoRA (no quantization), num_train_epochs 20, lr 2e-4, lora_r 16, lora_alpha 32, seed 42, T4 GPU
- Did I run the training myself (`executed_training_myself`): Yes (training time 224 s, final loss 0.0138 at step 40)
- Before training: `format_rate` = 0.095 (2/21) / `content_rate` = 0.000
- After training: `format_rate` = 1.000 (21/21) / `content_rate` = 0.905 (19/21)
- Regressed questions: None
- Failures remaining after training, and their type: 2 of 21 questions still failed the content check. One I confirmed is an unfounded assertion: the model gave a deadline with needs_review=false for a question not covered by the FAQ.
- Knowledge questions (Section 6), classification before -> after, and what I noticed:
  - Final assignment deadline: format_error -> asserted
  - Instructor's name: format_error -> needs_review
  - Next lecture's topic: format_error -> needs_review
  - Control (assignment deadline): format_error -> asserted
  - Before training, every output broke the JSON format. After training, the model asked for review on two of the unknown questions but still asserted a deadline for the one the FAQ does not cover.
- What training changed and what it did not: Training changed the output format (valid JSON with both keys on all 21 questions). It did not reliably change judgment on unknowns, because the model still asserted an answer to a question that is not in the FAQ.

## 宿題 (Homework)

**Level:** Basic

**Change:** num_train_epochs 20 -> 5 (everything else unchanged: lr 2e-4, lora_r 16, lora_alpha 32, seed 42). I restarted the session and ran from the top.

| Setting | Epochs | Steps | Training time | Last logged loss | format_rate | content_rate |
|---|---|---|---|---|---|---|
| Baseline | 20 | 40 | 224 s | 0.0138 (step 40) | 1.000 | 0.905 |
| Changed | 5 | 10 | 53 s | 1.570 (step 10) | 1.000 | 0.714 |

Before training (both runs): format_rate 0.095, content_rate 0.000. No regressions in either run.

**Observations:** With only 5 epochs (about 4x less training time), the model already followed the JSON format on all 21 questions. Content accuracy fell from 0.905 to 0.714, so the format is learned quickly, while exact wording and content need more training. In the 5-epoch run the model wrote a shorter "not in the FAQ" phrase than in the 20-epoch run, which may explain part of the content_rate drop (I did not verify this against the scoring code). In both runs the model still asserted an answer (needs_review=false) for the final-assignment deadline, which is not in the FAQ, so changing the number of epochs did not fix its judgment on unknowns. The 5-epoch run logged loss only once (step 10), so I could not compare final losses directly.

**When fine-tuning fits:** teaching a fixed output format or style quickly and cheaply.
**When it does not:** guaranteeing correct judgment on questions outside the training data, or keeping knowledge up to date. In those cases, retrieving from a source is more reliable.

**What I verified myself:** I ran both trainings in Colab on a T4 and took the numbers from the notebook output and the two `result.json` files. I used an AI assistant to help draft this text.
