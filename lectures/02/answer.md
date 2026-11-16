# Lecture 02 Answers

## Exercises

- **Model and settings used (from `config` in `result.json`):** Qwen/Qwen3.5-0.8B (revision: `2fc06364715b967f1860aea9cf38778875588b17`, seed: 42, lora_r: 16, lora_alpha: 32)
- **Did you run training yourself (`executed_training_myself`):** Yes
- **Knowledge Questions (Section 6) Before → After Classifications and Observations:**
  1. *Question:* この講座の最終課題の締切はいつですか
     - Before: `compliant structure / semantic content gap` (Output: `{"answer": "9 月 30 日 23:59"}`)
     - After: `asserted` (Output: `{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}`)
  2. *Question:* 担当教員の名前は何ですか
     - Before: `compliant structure / semantic content gap` (Output: `{"answer": "確認が必要"}`)
     - After: `needs_review` (Output: `{"answer": "この FAQ には記載がありません。運営に確認が必要です。", "needs_review": true}`)
  3. *Question:* 次回の講義のテーマは何ですか
     - Before: `compliant structure / semantic content gap` (Output: `{"answer": "次回の講義のテーマは... "}`)
     - After: `needs_review` (Output: `{"answer": "この FAQ には記載がありません。運営に確認が必要です。", "needs_review": true}`)
  4. *Question:* 課題の提出期限はいつですか
     - Before: `compliant structure / semantic content gap` (Output: `{"answer": "9 月 30 日 23:59"}`)
     - After: `asserted` (Output: `{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}`)
- **What changed and what stayed the same with training:** Structural format compliance remained consistent (Format Rate 1.0). While individual response examples demonstrated improved answer phrasing and review routing (`needs_review`), the overall automated aggregate metrics did not show a net content rate improvement between the 20-epoch baseline and 10-epoch experiment.

## Homework

- **Level attempted:** Basic
- **Settings changed:** Modified `num_train_epochs` from the baseline setting (20 epochs) to the experimental setting (10 epochs).
- **Result Files Preserved:** Both `result.json` (20-epoch baseline) and `result_10epochs.json` (10-epoch experiment) are provided in the directory for verification.

### Results Comparison Table (20 Epochs Baseline vs. 10 Epochs Experiment)

| Metric / Setting | Baseline Run (`result.json` - 20 Epochs) | Experimental Run (`result_10epochs.json` - 10 Epochs) |
| :--- | :--- | :--- |
| **Epochs (`num_train_epochs`)** | 20 | 10 |
| **Format Rate** | Before: 1.0 / After: 1.0 | Before: 1.0 / After: 1.0 |
| **Content Rate** | Before: 0.9048 / After: 0.9048 | After Training: 0.8095 |
| **Final Training Loss** | N/A (Logged in history) | 0.100067 (at Step 20) |
| **Evaluation Generation Time** | Before: 52.6s / After: 43.6s | 43.2s |

- **Discussion:** 
  - **Fine-tuning suitability:** Fine-tuning is effective when adapting a model to strict output formatting and structured domain-specific response patterns.
  - **Limitations / RAG comparison:** It is not suitable for dynamic or external knowledge that changes frequently; Retrieval-Augmented Generation (RAG) is preferable for handling external, evolving knowledge bases without retraining.
