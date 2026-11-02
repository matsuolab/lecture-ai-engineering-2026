# Lecture 02 Answers

## Exercises

- **Model and settings used:** Qwen/Qwen3.5-0.8B, LoRA fine-tuning without quantization, 20 epochs, 40 training steps, warmup_steps = 6, learning rate = 2e-4, LoRA rank = 16, LoRA alpha = 32, max sequence length = 512, seed = 42.
- **Did you run training yourself?** Yes. Completed all 20 epochs and 40 training steps on a Google Colab Tesla T4 GPU.
- **Before training:** format_rate = 95.24% / content_rate = 38.10%.
- **After training:** format_rate = 100% / content_rate = 90.48%.
- **Questions that regressed:** None. The evaluation reported an empty regression list.
- **Failures remaining after training and their types:** The final evaluation achieved 90.48% content accuracy (19 out of 21 cases). No regressions were reported.
- **Results of knowledge questions and observations:** The model continued to classify questions absent from the FAQ as `needs_review`, while answering the known deadline question as `asserted`. Fine-tuning improved the response wording without changing these classifications.
- **What changed and what stayed the same with training:** Format compliance improved from 95.24% to 100%, and content accuracy improved from 38.10% to 90.48%. The model learned the required answer format and improved its answers to FAQ questions.

## Homework

- **Level attempted:** Basic.
- **Settings or data changed:** Changed only the learning rate from 2e-4 to 1e-4. Kept the model, dataset, number of epochs (20), LoRA rank (16), LoRA alpha (32), warmup steps (6), and other settings unchanged.
- **Results (comparison tables or numbers):**

| Metric | Baseline (lr = 2e-4) | Experiment 2 (lr = 1e-4) |
|---|---:|---:|
| Training epochs | 20 | 20 |
| Training steps | 40 | 40 |
| Training time | 199 sec | 204 sec |
| Before format rate | 95.24% | 95.24% |
| After format rate | 100% | 100% |
| Before content rate | 38.10% | 38.10% |
| After content rate | 90.48% | 90.48% |
| Regressions | 0 | 0 |

- **Discussion of when fine-tuning is and is not suitable:** Fine-tuning is suitable when a model needs to follow a consistent response format, adapt to a specific task, or improve its behaviour on a domain-specific dataset. It is not a substitute for providing missing factual knowledge. If information is absent from the training data or source documents, fine-tuning alone cannot guarantee factual answers. Retrieval or confirmation from a reliable source is more appropriate in such cases.

**Observation:** Reducing the learning rate from 2e-4 to 1e-4 did not produce a measurable change in final format or content accuracy in this experiment. Training took approximately 5 seconds longer. This suggests that the original learning rate was already effective for this particular dataset and setup.
