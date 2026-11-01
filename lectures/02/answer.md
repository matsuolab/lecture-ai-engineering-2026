# Lecture 02 Answers

## Exercises

- Model and settings used (from `config` in `result.json`):
  - 20 epochs
  ```json
   {
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
  ```
- Did you run training yourself (`executed_training_myself`): Yes. I ran sections 0–8, including training and evaluation.
- Before training:
  - 20 epochs
  `format_rate` = 0.9523809523809523/ `content_rate` = 0.38095238095238093
- After training:
  - 20 epochs
  `format_rate` = 1.0/ `content_rate` = 0.9523809523809523
- Questions that regressed: No questions regressed after training.
- Failures remaining after training and their types (assertion without evidence / evasion through a confirmation request despite evidence being present / broken format): Question 21 (Do office hours require an appointment?) failed the content check after training. The model answered with an unsupported assertion.
- Results of knowledge questions (section 6; classification before → after training) and observations:
| Knowledge question | Before training | After training |
|---|---|---|
| When is the final assignment deadline for this course? | `asserted` | `asserted` |
| What is the instructor’s name? | `needs_review` | `needs_review` |
| What is the topic of the next lecture? | `needs_review` | `needs_review` |
| When is the assignment deadline? — control | `asserted` | `asserted` |

The response classifications did not change after training. However, I also found the post-training responses were clearer, more complete, and expressed in more fluent and natural language. Both before and after training, the model correctly set needs_review to true for questions about information clearly absent from the FAQ, such as the instructor’s name and the topic of the next lecture. However, when a question closely resembled information in the FAQ, the model continued to make an unsupported assertion. For example, it treated “the final assignment deadline” as equivalent to “the assignment deadline,” even though the FAQ did not establish that they referred to the same assignment.

- What changed and what stayed the same with training:
Both format compliance and content accuracy improved after training. The responses also became more fluent and natural. However, the model still made an unsupported assertion when a question closely resembled a question covered by the FAQ but asked for information that was not explicitly provided.

## Homework

- Level attempted: Basic
- Settings or data changed: I reduced `num_train_epochs` from 20 to 10 while keeping all other settings and the dataset unchanged. 
- Results (comparison tables or numbers):
- Results (comparison tables or numbers):

### Training and evaluation results

| Metric | 20 epochs | 10 epochs |
|---|---:|---:|
| Training steps | 40 | 20 |
| Final logged training loss | 0.014695 | 0.069153 |
| Training time (seconds) | 195 | 110 |
| Format compliance before training | 95.24% (20/21) | 95.24% (20/21) |
| Format compliance after training | 100% (21/21) | 100% (21/21) |
| Content accuracy before training | 38.10% (8/21) | 38.10% (8/21) |
| Content accuracy after training | 95.24% (20/21) | 90.48% (19/21) |
| Questions that regressed after training | 0 | 0 |

Content accuracy is based on the notebook's automated evaluation criteria.

### Section 6: Knowledge questions

| Question | Expected classification | Before training (both runs) | After 20 epochs | After 10 epochs |
|---|---|---|---|---|
| When is the final assignment deadline for this course? | needs_review | asserted | asserted | asserted |
| What is the instructor's name? | needs_review | needs_review | needs_review | needs_review |
| What is the topic of the next lecture? | needs_review | needs_review | needs_review | needs_review |
| When is the assignment deadline? (control) | asserted | asserted | asserted | asserted |

For the control question, an assertion supported by the FAQ is appropriate. For the final assignment deadline question, the assertion is unsupported because the FAQ does not explicitly identify the stated deadline as the final assignment deadline.
- Discussion of when fine-tuning is and is not suitable:
Fine-tuning is suitable for improving format compliance and can also improve content accuracy, as observed in this experiment. However, it does not guarantee correct answers when the provided FAQ lacks sufficient information. Therefore, fine-tuning alone is not sufficient for ensuring reliable answers to such questions; additional information or human review is needed.
