# Lecture 02 Reference Results (Run by the Instructor on a T4)

These reference results come from the original Japanese notebook. Results for the translated exercise have not been remeasured.

If you cannot get a GPU or cannot finish training in time, follow **4b** of the notebook (`notebooks/lora_format_tuning.ipynb`) and use these results for comparison and discussion.
When submitting, set `executed_training_myself` in section 7 to `False` and describe in `lectures/02/answer.md` how far you ran the notebook yourself.

| File | Contents |
|---|---|
| `result.json` | Settings (`config`), library versions, before/after summaries (`before` / `after`), regressed questions, and knowledge-question results |
| `eval_before.json` | Original outputs and scores for the 21 questions before training |
| `eval_after.json` | Original outputs and scores for the 21 questions after training |

- Open the files on GitHub or save them with "Download raw file"
- GPU training is not perfectly reproducible even with the same seed, so it is normal for your "remaining questions" to differ. Compare failure types
