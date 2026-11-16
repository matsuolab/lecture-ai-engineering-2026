# Lecture 02 Exercises and Homework: Learn an Answer Format with LoRA and Compare Before and After Training

Use Google Colab (T4 GPU, free tier) for this session. You will not use Codespaces.

## Goals for This Session

- Briefly train a small model with LoRA and use numbers and outputs to check **what changes and what stays the same** before and after training
- Explain from your own results that "training can teach a format, but does not guarantee sound judgment about unknown information (whether to request confirmation or make an assertion)"
- Explain in your own words when fine-tuning is and is not suitable

## Notebook

- [notebooks/lora_format_tuning.ipynb](../../notebooks/lora_format_tuning.ipynb)
- Open in Colab: https://colab.research.google.com/github/matsuolab/lecture-ai-engineering-2026-en/blob/main/notebooks/lora_format_tuning.ipynb

Using a fictional course FAQ (5 items), train `Qwen/Qwen3.5-0.8B` with LoRA for 20 epochs (20 passes over 14 training examples, 40 steps; 4–5 minutes on a T4).
The desired output is one JSON line: `{"answer": ..., "needs_review": ...}`. For questions absent from the FAQ, the correct response is to say "Confirmation is needed" with `needs_review: true`.
Evaluation separates **format compliance rate** (whether the output follows the JSON format) and **content accuracy** (whether `needs_review` and answer keywords match the expected answer). The timing and output observations in these instructions come from the original Japanese exercise on a T4; results may differ with the translated FAQ and questions, which have not been remeasured.

## Preparation (Optional, 5 Minutes)

Running sections 0–3 before class to check GPU allocation, library installation, and model downloading will help avoid delays during class.
Colab loses variables when the session disconnects, so start again from section 0 on the day.

## Exercises (30 Minutes)

1. Open the notebook in Colab and select **File → Save a copy in Drive** to make your own copy
2. Select **Runtime → Change runtime type → T4 GPU**
3. Run sections 0–3 in order (about 5 minutes). In the before-training table, check **which keys are missing** and whether the wording agrees with the FAQ
4. Train in section 4 (4–5 minutes). While waiting, read the explanation of "LoRA versus QLoRA". Check `trainable%` and how `Training Loss` changes
5. Evaluate after training in sections 5–6 and compare with before training
   - Comparison table: how did `format_rate` and `content_rate` change?
   - `Regressions`: questions that passed before training but failed afterward (ideally the list is empty; inspect any regressions in your own run)
   - Remaining failure types: did it **assert** an answer by applying a different FAQ item to a question absent from the FAQ, or **evade** a question covered by the FAQ by saying "It is not listed"?
   - Section 6: did it request confirmation or make an assertion for questions absent from both the FAQ and training data?
6. Create `result.json` in section 7. Record the key points in `lectures/02/answer.md` and open a PR from working branch `lec02` to `main` in your own fork (you may edit answer.md in GitHub's web interface). You may place `result.json` in `lectures/02/` and include it in the PR
7. Select **Runtime → Disconnect and delete runtime**

> Colab's free tier limits GPU usage time. Always delete the runtime when you finish.
> If you cannot get a GPU or cannot finish training in time, follow section 4b of the notebook and compare and discuss the instructor's T4 results. When submitting, set `executed_training_myself` to `False` and describe in answer.md how far you ran the notebook yourself.

Even with a fixed seed, GPU training is not perfectly reproducible. It is normal for your "remaining questions" to differ from your classmate's; compare failure types instead.

## Homework (Complete Any One Level)

| Level | Task |
|---|---|
| Basic | Change one of `lora_r`, `lr`, or `num_train_epochs` in `CONFIG`, retrain, and record `format_rate`, `content_rate`, final loss, and training time alongside the original settings. After changing a setting, select **Runtime → Restart session** and run from the top (because the trained model remains in memory). Compare the two `result.json` files |
| Implementation | Replace `FAQ`, `GROUNDED`, and `UNGROUNDED` with your own topic (about 5 items), train, and compare before and after. Keep the JSON format and `needs_review` design. Describe how you prepared questions "without evidence" |
| Advanced | Use `scripts/make_sft_dataset.py` to make Q&A data (JSONL in `messages` format) from the course glossary, and train on it instead of the FAQ. Prepare your own evaluation questions (terms in the glossary, paraphrased questions, and terms absent from the glossary) and expected answers, then compare before and after training. Compare with a mechanism that searches the glossary, and discuss the advantages and disadvantages of training the model |

Creating data for the advanced homework (run in Codespaces and upload the resulting file to Colab):

```bash
uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl
```

In Colab, each line uses the same `messages` format as the notebook's `to_chat`, so pass the loaded records directly to `Dataset.from_list` and train with `SFTTrainer` in section 4. Rebuild the evaluation (`test` and `gold`) yourself to match the glossary.

Section 8 (load in 4-bit and compare outputs) is an observation without training, so you may include its results at any homework level. Training in 4-bit (QLoRA) has not been verified in this course environment (T4), so it is outside the homework scope.

## Notes

- After training, variable `model` also has the adapter inserted. To regenerate before-training outputs, use `tuned.disable_adapter()` (see section 6) or restart the session
- Notebook libraries are pinned to verified versions (`PINS` in section 0). Changing versions may break the notebook
