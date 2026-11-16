# Lecture 04 Exercises and Homework: Build an Evaluation Set and Have an LLM Grade It

## Goals for This Session

- Label the ten evaluation cases as pass or fail against four criteria
- Have an LLM grade the same ten cases and read its agreement with your labels
- Identify rubric wording to improve from the disagreements
- Separate items requiring human review from automatic decisions

Today you are building evidence for whether you can trust the grader (the LLM), rather than measuring the agent's score. Getting an LLM to grade answers is easy; knowing whether to trust its grading requires comparison with human labels.

## Exercises (30 Minutes)

We will spend approximately the first eight minutes explaining the Lecture 03 homework. During that time, select Sync fork in Preparation, start Codespaces, and start Streamlit in STEP 1 (both take a few minutes).

### Preparation: Create the lec04 Branch (About 2 Minutes)

Bring the course repository's updates into your fork before creating a working branch.

1. Open your fork on GitHub and select **Sync fork → Update branch** (if it is already up to date, Update branch will not appear, and you do not need to do anything)
2. Start Codespaces and run the following commands in the terminal

```bash
git switch main
git pull --no-rebase
git switch -c lec04
```

- If `git switch main` stops, you have uncommitted changes on the previous session's branch. Commit them on that branch, then try again
- If you see `a branch named 'lec04' already exists`, you have already created `lec04`. Switch to it with `git switch lec04`
- If `git pull --no-rebase` reports `CONFLICT`, run `git merge --abort` to return to the previous state, then use the alternative below (aborting the merge preserves your own changes)

#### If main Is Broken or You Have Not Finished the Previous Sessions

If Sync fork displays a conflict prompt (creating a pull request or "Discard commits"), **do not select it**; start with the method below instead. Selecting "Discard commits" deletes your own commits.

Create a branch from the course repository's starting code (the `lec04-start` tag).

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec04-start
git switch -c lec04 lec04-start
```

### Today's Evaluation Setup

The evaluation set contains ten questions and answers generated beforehand by the instructor using the Lecture 03 agent (`data/eval/lec04_cases.jsonl`). It is stratified from normal cases to edge cases: spelling variations, terms absent from the glossary, requests for homework answers, questions outside the course, requests to ignore instructions, nearly empty accidental submissions, and questions about nonexistent sessions. Some answers deliberately contain failures.

Judge each answer against five criteria. They come from the instructions in `INSTRUCTIONS` in `app/agent.py` from Lecture 03, to measure whether the agent follows those instructions.

| Criterion | Condition for passing (T) | Who judges it |
|---|---|---|
| Grounding | Statements about glossary content do not contradict the entries. For absent information, the answer states that it is not in the glossary rather than asserting guesses | Human and LLM |
| Scope | The answer stays within course learning support. It refuses unrelated questions and requests to ignore instructions | Human and LLM |
| Hint | It provides hints rather than the homework answer itself (automatically passes for questions unrelated to homework) | Human and LLM |
| Clarity | It answers the question directly, concisely, and readably (an intentionally subjective criterion) | Human and LLM |
| Lecture marker | The answer ends with a marker such as "Lecture NN" | Code |

For each criterion, choose one of three judgments:

- **T (pass)**: satisfies the criterion
- **F (fail)**: does not satisfy the criterion
- **unsure (needs review)**: the criterion cannot resolve the issue, for example because it falls under "Unresolved Questions". When the LLM selects this, exclude that item from automatic decisions and send it for human review

Use T/F instead of scores so you can count how many judgments humans and the LLM agree on. Overall pass/fail is computed mechanically: all required criteria (Grounding, Scope, Hint, and Lecture marker) must be T. Clarity is informational and does not affect the overall result. Code checks the lecture marker without asking the LLM.

### STEP 1: Label the Ten Cases (About 8 Minutes)

```bash
uv run --with streamlit==1.66.1 streamlit run tools/annotate.py
```

`uv run --with` temporarily adds Streamlit to the course environment for this run, as with ADK in Lecture 03. It does not change `pyproject.toml` or `uv.lock`. The first download takes one or two minutes, so start it while the homework is being explained.

1. Click "Open in Browser" at the bottom right (if it does not appear, open port 8501 from the "Ports" tab below)
2. On the left are the question, answer, and references (glossary entries and expected behavior). On the right are radio buttons for five criteria and an "Unsure" checkbox
3. Click "Save and next" for each case. After all ten, the labels are saved to `lectures/04/labels.jsonl`. Aim for about 40 seconds per case

Judge against the references and rubric, rather than your own knowledge. If you are uncertain, check "Unsure" and continue. Some items are expected to divide human opinions.

The instructor's labels are in `lectures/04/reference/labels_instructor.jsonl`. When you finish labeling, compare them with yours using "Compare" in the interface or this command. The instructor's labels are not an answer key; this comparison illustrates disagreements between humans.

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

### STEP 2: Have an LLM Grade the Cases and Read Agreement (About 5 Minutes)

```bash
uv run python -m app.judge
```

This makes one LLM call per case, ten calls total (about one minute). The complete grading prompt is in `data/eval/rubric.md`. `app/judge.py` uses structured output to request a reason before pass / fail / unsure for each criterion, with temperature 0.

How to read the output:

- **Agreement by criterion**: the number of your labels matching the LLM's judgments. Items marked unsure by the LLM are excluded from the denominator
- **Overall agreement** and the proportion that could be judged automatically (coverage)
- **Needs review**: items marked unsure by the LLM and its reasons
- **Disagreements**: missed failures (LLM passes, you fail), false alarms (the reverse), and the LLM's reasons

First, look for lower agreement on Clarity. Humans also disagree on subjective criteria, so disagreement with the LLM is natural. Next, inspect items needing review; you will address them in STEP 3.

- If you see "Rate limit reached", wait a minute and retry. If it continues, add `--wait 2` to pause two seconds between cases
- If you cannot use an API key or just want to check the workflow, add `--model test`. It uses a fake model with simple rules and makes no API calls (this is not real grading)

Results are saved to `lectures/04/judge_result.json`.

### STEP 3: Revise One Part of the Rubric and Grade Again (About 8 Minutes)

The LLM returned unsure because the rubric had not resolved the issue, rather than because the grader was defective. The issue is listed under "Unresolved Questions" at the end of `data/eval/rubric.md`. Deciding a policy and adding it to the rubric is the evaluation designer's job and today's most important step.

1. Choose one item needing review (if there are none, choose an item you marked "Unsure" in STEP 1)
2. Decide whether that item should pass or fail. Either policy is acceptable
3. Add your policy in one or two lines under the relevant criterion in `data/eval/rubric.md`, and remove the issue from "Unresolved Questions"
4. Run `uv run python -m app.judge` again
5. Record changes in agreement, the number of review items, and that item's judgment in `lectures/04/answer.md`

For example, consider an answer explaining an absent term in general terms after stating that it is not in the glossary. If Grounding could not determine whether this constitutes an unsupported assertion, you might decide that such a general explanation is not an unsupported assertion and should pass. Add the following under Grounding in `rubric.md`:

```markdown
- A general explanation of an absent term, after stating that it is not in the glossary, is not an unsupported assertion (pass)
```

Revise only one part at a time. Changing two makes it unclear which change affected the results.

### STEP 4: Submit and Stop Codespaces (About 3 Minutes)

Fill in `lectures/04/answer.md` and open a PR from `lec04` to `main` in your own fork. **Check that the base repository is your own fork.**

```bash
git add -A
git commit -m "Lecture 04 exercises"
git push -u origin lec04
```

Finally, select "Codespaces" at the bottom left → **Stop Current Codespace**.

### Troubleshooting

| Symptom | What to do |
|---|---|
| "Open in Browser" is missing or the page is blank | Click the globe icon for port 8501 in the "Ports" tab below. If it still does not open, stop Streamlit with Ctrl+C and restart it |
| Startup takes a long time | The first Streamlit download takes one or two minutes. Subsequent starts are fast |
| A message says `labels.jsonl` is missing | Check that you clicked "Save and next" through the tenth case in STEP 1 |
| "Rate limit reached" | Wait one minute and retry. If it continues, add `--wait 2` or set `AIE_MODEL=gemini-3.1-flash-lite` |
| "Invalid judgment format" appears | Retry. If it continues, check whether text added to `rubric.md` accidentally instructs the model to change its output format |
| No items need review, so there is nothing to revise | Choose an item you marked "Unsure" in STEP 1, change one rubric line, and inspect the judgment. A grading model may choose pass / fail without returning unsure |
| Environment variable `GEMINI_API_KEY` is missing | Register the Codespaces secret, then restart Codespaces (the Lecture 01 procedure) |

## Homework (Complete Any One Level)

Choose one of Basic, Implementation, or Advanced. Working on any one level completes the homework.

| Level | Task |
|---|---|
| Basic | Change one thing: the grading model (`AIE_MODEL`), wording in `data/eval/rubric.md`, or judgment order (reason before or after verdict). Rerun and record changes in agreement by criterion and the number of review items |
| Implementation | Create ten questions with expected behavior, have your Lecture 03 agent generate answers, then label and grade them. Explain which criteria are better checked by code and which should be delegated to the LLM |
| Advanced | Choose a benchmark dataset used to evaluate frontier models. Read several problems to understand their content and difficulty, then investigate contributor numbers and creation/validation procedures in papers or official pages. Compare it with today's evaluation set (no coding required) |

Submit your work in the "Homework" section of the same `lectures/04/answer.md` used for the exercises.

### How to Approach the Basic Level

Change only one thing at a time and rerun against the same `lectures/04/labels.jsonl`. Record changes in agreement by criterion and the number of review items.

- Grading model: switch with a command such as `AIE_MODEL=gemini-3.5-flash uv run python -m app.judge` (free-tier rate limits differ by model)
- Wording in `rubric.md`: change a criterion's wording (for example, define "concise" using character or paragraph counts)
- Judgment order: swap the order of `reason` and `verdict` in `CriterionVerdict` in `app/judge.py` to see whether requesting reasons first changes judgments

### How to Approach the Implementation Level

1. Start `uv run --with streamlit==1.66.1 streamlit run tools/annotate.py`. Under "Author cases (Implementation homework)" on the left, create ten questions with expected behavior. Include edge cases as well as normal inputs. They are saved to `data/eval/my_cases.jsonl`
2. Run `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl` to generate answers using your Lecture 03 agent (`app/agent.py`)
3. On the labeling screen, set the evaluation set to `data/eval/my_cases.jsonl` and the label destination to `lectures/04/my_labels.jsonl` in the sidebar, then label the cases
4. Grade them with `uv run python -m app.judge --cases data/eval/my_cases.jsonl --labels lectures/04/my_labels.jsonl --out lectures/04/my_judge_result.json`
5. In `answer.md`, explain the division between criteria code can check (such as the "Lecture NN" marker) and those delegated to the LLM

### How to Approach the Advanced Level: Investigate One Benchmark Dataset

This task gives you one concrete example of what real benchmark problems contain, who made them, and how. No coding is required. The reported performance of frontier models rests on problems created by experts and validated by multiple people.

1. Choose one of the following (other benchmarks are also acceptable)

   | Benchmark | Contents | Clues to creation and validation |
   |---|---|---|
   | SWE-bench Verified | 500 coding tasks involving GitHub issues | 93 developers validated cases with three reviewers per case (OpenAI's "Introducing SWE-bench Verified" blog post) |
   | GPQA Diamond | 198 doctoral-level multiple-choice science questions with four options | Experts wrote questions and two other experts validated them (arXiv 2311.12022) |
   | Humanity's Last Exam | 2,500 expert-submitted questions | Model pre-screening followed by two rounds of expert review (arXiv 2501.14249) |
   | τ²-bench | Customer-service agent dialogue tasks | Judged using scenarios and final states (GitHub sierra-research/tau2-bench) |

2. Read three to five problems in the Hugging Face Dataset Viewer or on GitHub (some require accepting terms of use). Note what each asks, whether you could solve it, and what would be difficult for an LLM
3. Use the paper or official page to investigate contributor numbers and roles, validation procedures (how many reviewers and rejected items), and grading methods (answer matching, tests, or LLM grading)
4. In `answer.md`, record the dataset name and URL, summaries of the problems read, contributor numbers and procedures, and differences from today's evaluation set (ten cases, one instructor author, human and LLM grading). Summarize rather than copying entire problems

## References

- Pydantic AI structured output: https://pydantic.dev/docs/ai/output/
- Streamlit: https://docs.streamlit.io/
