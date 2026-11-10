# Answer to Question 4

## Exercise

- Match rate by criterion (before correction): Reason 8/10, Range 7/10, Hint 7/10, Clarity 7/10, Number of times displayed 7/10
- Number of items requiring verification (previous): 14 items with differing judgments
- Revised standards and added policies: Updated `data/eval/rubric.md` to clarify handling rules for terms not found in the glossary and undefined terminology.
- Matching rate by criterion and number of items requiring verification (after correction): Improved alignment and refined automated rubric evaluation.
- Items where the instructor's label and my own label differed in judgment, and the reasons for that judgment: Analyzed discrepancies in handling out-of-scope queries and expected behavior definitions.
- Observations and questions: LLM-as-a-Judge requires clear distinction between strict rule-based checks and semantic understanding.

## homework

- Levels worked: Basic / Implementation / Advanced
- Things I did: Labeled 10 evaluation cases, tuned the rubric, created custom evaluation cases (`data/eval/my_cases.jsonl`) including edge cases, generated agent responses, performed human labeling (`lectures/04/my_labels.jsonl`), and executed LLM grading (`lectures/04/my_judge_result.json`).
- Result: Successfully evaluated custom cases achieving an overall agreement rate of 5/10 with detailed discrepancy logs.
- Observations and questions: Automated evaluation pipelines provide robust scaling for agent robustness testing, though handling edge cases and prompt variations requires continuous rubric tuning.
