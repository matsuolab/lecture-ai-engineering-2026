# Lecture 04 Reference Material

- `labels_instructor.jsonl`: labels assigned by the instructor. Each `note` explains the judgment and any deliberately introduced failure.
  The instructor's labels are not an answer key. They illustrate that humans also disagree on some items.

To compare them with your labels (`lectures/04/labels.jsonl`), use the "Compare" screen in `tools/annotate.py` or this command:

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

## Findings from Grading with the Real Model (gemini-3.5-flash-lite)

The following observations come from the original Japanese exercise, running `app.judge` with the instructor's labels as "your labels". They led to revisions to `rubric.md` and the evaluation set. Grading with the translated English data has not been verified with a real LLM.

| Observation | Revision |
|---|---|
| #02 Grounding: failed the answer because the reference's expected behavior said to end with "Lecture 03" (the lecture marker is checked by code) | Removed the final "Lecture N" requirement from expected behavior and added a rubric instruction to exclude that marker from these judgments |
| #06 and #08 Clarity: carried reasons for failing Hint or Scope into Clarity and failed it too | Added "Judge only readability; other criteria cover content and role" under Clarity, and "Judge each criterion independently" in the grading instructions |
| #04 Clarity: passed a verbose answer that repeated the same explanations | Made the rule concrete: excessive paraphrasing or repetition of the same content, such as repeating an explanation with "In other words", fails |
| #05 Grounding: returned pass instead of unsure, deciding an issue the rubric had not resolved | Added "Unresolved Questions" at the end of the rubric, explicitly requiring unsure for answers covered there. In STEP 3, decide a policy for this issue and add it to the criterion |

Grading models tend to choose pass / fail even for issues the rubric has not resolved. Before class, run the revised rubric again and check whether #05 receives unsure.
