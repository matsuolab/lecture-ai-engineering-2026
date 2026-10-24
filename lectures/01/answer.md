# Lecture 01 Answers

## Exercises

- Model's answer to the course-specific question:
  It said it doesn't know the AIE2026 course and asked for more context.
- What you noticed when comparing it with the correct meaning in the glossary:
  The glossary says the levels are Basic, Implementation, Advanced. The model gave none of them.
- Token counts you displayed (input / output):
  18 / 50 for the AIE2026 homework-levels question (gemini-3.5-flash-lite).

## Homework

- Level attempted: Advanced ,Basic, Implementation, 
- What you did:
  - Basic: ran "What is LoRA?" 3 times on each of gemini-3.5-flash-lite and gemini-3.8-flash (`uv run python -m app.ask basic`).
  - Implementation: added a chat mode to `app/ask.py` using `client.chats.create`, which keeps the history for follow-up questions (`uv run python -m app.ask implementation`).
  - Advanced: timed each call and printed token counts for 2 questions on 2 models. Saved in `results.csv` (`uv run python -m app.ask advanced`).
- Results:

### Basic
Question: "What is LoRA?", 3 runs per model.
  - gemini-3.5-flash-lite: all 3 runs gave the same definition (Low-Rank Adaptation) and the same structure (problem, how it works, benefits, uses). The analogy changed every run: a transparent sheet over a painting, a car with a new steering wheel cover, sticky notes in a textbook. Only run 3 said Microsoft developed it. Run 2 had a typo ("LoRs"). None of the runs mentioned LoRa the radio technology.
  - gemini-3.8-flash: all 3 runs also gave the same AI definition. Runs 1 and 3 added a note at the end about LoRa (Long Range) for IoT. Run 2 opened by saying LoRA has two meanings and covered both in separate sections, with no analogy. Run 1 mentioned QLoRA and the A and B matrices.
  - Between models: the facts agree. 3.8-flash always mentioned the IoT meaning and flash-lite never did. Wording, analogy and length change from run to run on both models, but the core answer does not.

### Implementation
Chat mode with history worked. I asked 3 questions in one session:
  1. "Give me 3 examples of fine-tuning methods." It listed Full Fine-Tuning, LoRA (PEFT) and Feature Extraction.
  2. "Which of those is the cheapest?" It answered Feature Extraction (and noted LoRA as the best-value option), so it understood "those" from the previous answer.
  3. "Why?" It explained why Feature Extraction is cheapest (no gradients for the base model, smaller optimizer states, less time), so it kept the context of both earlier turns.
  - Input tokens grew each turn: 144, 615, 791. Each input equals the previous input + previous output + the new question (144 + 462 + 9 = 615; 615 + 172 + 4 = 791). This shows the full history is sent again every turn. The 144 on the first question here is more than the question alone, so earlier turns were probably already in that session.

### Advanced

| model | question | seconds | input tok | output tok | total tok |
|---|---|---|---|---|---|
| gemini-3.5-flash-lite | What is LoRA? | 3.37 | 6 | 748 | 754 |
| gemini-3.5-flash-lite | Explain overfitting in two sentences. | 0.95 | 7 | 54 | 61 |
| gemini-3.8-flash | What is LoRA? | 49.03 | 6 | 834 | 1718 |
| gemini-3.8-flash | Explain overfitting in two sentences. | 17.68 | 7 | 47 | 407 |

- Observations:
  - gemini-3.8-flash took 18-49 s per call; gemini-3.5-flash-lite took 1-3 s.
  - Output length was similar on both models, so the time difference is not from output length.
  - The short "two sentences" question used far fewer output tokens than the LoRA question on both models.
  - gemini-3.8-flash total tokens (1718, 407) are much higher than input + output (840, 54).
  - gemini-3.8-flash used about 2x to 7x more tokens than flash-lite (1718 vs 754, 407 vs 61), so it would hit free-tier token limits much sooner.
 
