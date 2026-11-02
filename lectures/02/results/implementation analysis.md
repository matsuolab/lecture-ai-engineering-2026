## Homework: Implementation level (own topic: gym FAQ)

### What I changed
I replaced `FAQ`, `GROUNDED`, `UNGROUNDED` (and the test-only extras) with a
5-item FAQ for a fictional gym: opening hours, membership fee, free trial,
facilities, and cancellation. I kept the JSON output format and the
`needs_review` design. The ungrounded answer now says confirmation from the
gym staff is needed. Training settings were unchanged except `lora_r`, which I
set to 26 (default 16).
I ran the training myself: executed_training_myself = True.

### How I prepared questions "without evidence"
I wrote gym questions that sound natural but whose answers appear nowhere in
the 5 FAQ entries (lockers, dress code, protein powder, group classes,
trainer assignment). Several deliberately overlap in wording with an FAQ
item, to test whether the model asserts a nearby entry instead of asking for
confirmation: "refund if I cancel mid-month" (vs. cancellation), "book
machines in advance" (vs. trial reservation), "bring a friend for free"
(vs. free trial). They were split across train, valid and test so the test
questions were never seen in training. For section 6 I used questions absent
from both the FAQ and the training data, plus one covered control question.

### Results
| | format_rate | content_rate |
|---|---|---|
| Before training | 1.0 | 0.238 |
| After training | 1.0 | 0.810 |

trainable% = 1.36, training time = 243 s, regressions = none.

### What changed and what stayed the same
- Format was already perfect before training (1.0), so training did not
  improve format here. The prompt alone was enough for this model.
- Content improved a lot. Before training, the model often set
  `needs_review` wrongly (e.g. true for covered questions, false for
  uncovered ones) and gave short fragments like "Yes" or "4,500 yen".
  After training it answered in the FAQ's wording with the right flag.

### Remaining failures (4 of 21)
- Asserted instead of requesting confirmation (2): "Will I get a refund if I
  cancel mid-month?" got the cancellation answer, and "Do I need to book
  machines in advance?" got the trial answer, both with needs_review=false.
  The model reused a different FAQ item that shares words with the question.
- Keyword misses (2): the Sunday-hours and general-member-fee answers were
  correct but shortened, so they lacked a required keyword. This is partly a
  limitation of the scoring rule.
- No evasions (saying "not listed" for a covered question).

### Section 6 (absent from FAQ and training data)
[Fill in after rerunning with gym questions: which became needs_review,
which stayed asserted, and what the asserted ones relied on.]

### Conclusion
Training taught the model to answer in the expected style and wording, but
it did not teach it to judge whether the FAQ contains the evidence.
Questions that resembled an FAQ item still got confident, wrong answers.
Fine-tuning suits fixing format, tone and consistent wording; for new or
changing knowledge, or for deciding when to say "I don't know", prompts,
RAG and evaluation are better first steps.