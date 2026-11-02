# Lecture 02 Answers

## Exercises

- Model and settings used (from `config` in `result_for_exercise.json`): `Qwen/Qwen3.5-0.8B` (revision `2fc06364`), LoRA without quantization, `lora_r` = 16, `lora_alpha` = 32, `lr` = 2e-4, `num_train_epochs` = 20, `warmup_steps` = 6, `max_seq_len` = 512, `max_new_tokens` = 96, greedy decoding, seed 42, on the course FAQ (5 items).
- Did you run training yourself (`executed_training_myself`): **Yes** (I ran the notebook myself on Colab).
- Before training: `format_rate` = 0.952 (20 of 21) / `content_rate` = 0.381 (8 of 21)
- After training: `format_rate` = 1.000 (21 of 21) / `content_rate` = 0.952 (20 of 21)
- Questions that regressed: none (`regressed` is empty).
- Failures remaining after training and their types (assertion without evidence / evasion through a confirmation request despite evidence being present / broken format):
  - 1 of 21 evaluation questions still fails the content check. **[Fill in which question and its type from the section 6 table in the notebook; `result.json` does not record it.]**
  - Broken format: none after training. Before training, 1 output broke the JSON format; training fixed it.
- Results of knowledge questions (section 6; classification before → after training) and observations:

  | Question | In FAQ | Before | After |
  |---|---|---|---|
  | When is the final assignment deadline for this course? | no | asserted | **asserted** (September 30 23:59) |
  | What is the instructor's name? | no | needs_review | needs_review |
  | What is the topic of the next lecture? | no | needs_review | needs_review |
  | When is the assignment deadline? | yes | asserted | asserted (correct) |

  Observations: “final assignment deadline” is not in the FAQ, but it is similar to the covered “assignment deadline” item. Before and after training, the model gave that item’s answer (September 30) with needs_review: false. So training did not teach it to notice that the evidence was missing. For the two unrelated questions (instructor, next lecture), the flag was already correct before training; only the wording changed, to the standard sentence “This FAQ does not contain that information. Confirmation from the course organizers is needed.”
- What changed and what stayed the same with training:
  - **Changed:** content accuracy went from 0.381 to 0.952 and format compliance from 0.952 to 1.0. Answers now use the FAQ's wording and the fixed confirmation sentence, with no regressions.
  - **Stayed the same:** for a question that resembles a covered item but is not covered, the model still asserts a nearby answer. Training taught the format and wording but did not give the model judgment about whether the FAQ contains the evidence.

## Homework

- Level attempted: **Implementation**, **Basic**, and **Advanced** (all three are described below; any one of them satisfies the requirement).

### Implementation level (own topic: gym FAQ)

- Settings or data changed: I replaced `FAQ`, `GROUNDED`, and `UNGROUNDED` with a 5-item FAQ for a fictional gym (opening hours, membership fee, free trial, facilities, cancellation). I kept the JSON format and the `needs_review` design. The "no evidence" answer now says confirmation from the gym staff is needed. Training settings were unchanged except `lora_r` = 26 (default 16).
- How I prepared questions "without evidence": I wrote natural gym questions whose answers appear nowhere in the 5 FAQ entries (lockers, dress code, protein powder, group classes, trainer assignment). Several deliberately overlap in wording with an FAQ item to test whether the model asserts a nearby entry: "refund if I cancel mid-month" (vs. cancellation), "book machines in advance" (vs. trial reservation), "bring a friend for free" (vs. free trial). They were split across train, valid, and test so test questions were never seen in training.
- Results (from `result_for_implemetation.json`):

  | | format_rate | content_rate |
  |---|---|---|
  | Before training | 1.000 | 0.238 (5/21) |
  | After training | 1.000 | 0.810 (17/21) |

  trainable% = 1.36, training time = 243 s, regressions = none.
- Remaining failures (4 of 21):
  - Assertion instead of confirmation (2): "Will I get a refund if I cancel mid-month?" got the cancellation answer, and "Do I need to book machines in advance?" got the trial answer, both with `needs_review: false`. The model reused a different FAQ item that shares words with the question.
  - Keyword misses (2): the Sunday-hours and general-member-fee answers were correct but shortened, so they lacked a required keyword. This is partly a limitation of the scoring rule.
  - Evasion (saying "not listed" for a covered question): none.
- Section 6 (questions absent from both the FAQ and the training data):

  | Question | Before | After |
  |---|---|---|
  | When is the final assignment deadline for this course? | needs_review | **asserted** (answered with the cancellation rule, wrong) |
  | What is the instructor's name? | needs_review | needs_review |
  | What is the topic of the next lecture? | needs_review (but the answer was the gym opening hours) | needs_review (standard confirmation sentence) |
  | When is the assignment deadline? | needs_review | **asserted** (answered with the cancellation rule, wrong) |

  Training fixed the wording (the “next lecture” answer changed from unrelated opening hours to the standard confirmation sentence). But 2 of the 4 questions went from correctly flagged to wrongly asserted: both “deadline” questions got the cancellation rule (“by the 20th of the month”). The model matched on the word “deadline” and did not check whether the FAQ actually had the answer.
- Discussion of when fine-tuning is and is not suitable: Training taught the model the expected style and wording, but not whether the FAQ contains the evidence. Questions that resembled an FAQ item still got confident, wrong answers, and training even turned two correct "needs review" responses into assertions. Fine-tuning suits fixing format, tone, and consistent wording. For new or changing knowledge, or for deciding when to say "I don't know", prompts, RAG, and evaluation are better first steps.

### Basic level (change `lora_r`)

- Settings changed: `lora_r` 16 → 26 (`lora_alpha` stayed 32, so the LoRA scaling `alpha/r` dropped from 2.0 to about 1.23). Everything else was unchanged (20 epochs, lr 2e-4), on the course FAQ.
- Results (`result_for_exercise.json` vs `result_for_basic.json`):

  | | lora_r | format_rate (before → after) | content_rate (before → after) |
  |---|---|---|---|
  | Original | 16 | 0.952 → 1.000 | 0.381 → **0.952** (20/21) |
  | Changed | 26 | 0.952 → 1.000 | 0.381 → **0.905** (19/21) |

  Regressions: none in either run. Section 6 classifications were identical in both runs (the "final assignment deadline" question was asserted in both).
- Observation: A larger rank did not help. With lora_r = 26 the model got 19 of 21 questions right, versus 20 of 21 with lora_r = 16. That is only one question, so it is probably just random variation between runs. The format result was the same (100%), and the section 6 answers were the same too. This FAQ is small (5 items) and the answer style is fixed, so the model did not need the extra capacity.

### Advanced level (glossary Q&A instead of the FAQ)

- Settings or data changed: I used `scripts/make_sft_dataset.py` to make Q&A data from the course glossary (116 examples in `messages` format) and trained on it instead of the FAQ. Settings: `lora_r` = 16, `lora_alpha` = 32, `lr` = 2e-4, 5 epochs (75 steps), same base model. Training time 155 s, final loss 0.237. I built my own evaluation of 15 questions: 5 glossary terms (Epoch, Overfitting, temperature, LoRA, Rate limit), 5 paraphrased questions (same concepts without the glossary wording, plus the 429 error), and 5 terms absent from the glossary (Docker, gradient descent, RLHF, vector database, and the fictional Zorvani protocol). Free-text answers are scored by keywords, so there is no `format_rate`.
- Results (from `result(1).json`, `executed_training_myself` = true):

  | | glossary (of 5) | paraphrase (of 5) | absent (of 5) | content_rate |
  |---|---|---|---|---|
  | Before training | 5 | 1 | 0 | 0.400 (6/15) |
  | After training | 5 | 2 | 0 | 0.467 (7/15) |

  Regressions: none.
- What changed: the only gain was one paraphrase question ("Why can the same question give different answers?"), which now mentions randomness in generation. Answers moved toward the glossary's style and brevity. Glossary terms were already 5/5 before training, so there was nothing to gain there.
- What stayed the same, and remaining failures: all 5 absent terms still received a confident answer (none declined), including the invented "Zorvani protocol" (before: "Version 1.0 released in October 2026"; after: "Version 2.0 introduces environment variables"). The paraphrased questions about overfitting, LoRA, and the 429 error mixed correct parts with invented details (for example, "bottom k eigenvectors" for LoRA). These are all assertions without evidence. There was no evasion and no broken format. The +1 is within the noise of a 15-question test, and the keyword scoring is loose: "What do we call one full run through the training data?" passed both times even though "one fit" and "training step" are wrong (the term is *epoch*).

