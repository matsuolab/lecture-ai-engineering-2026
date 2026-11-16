# Lecture 01 Exercises and Homework: Set Up Your Development Environment and Ask an LLM

## Goals for This Session

- Open your own fork in Codespaces and call the Gemini API
- Make small code changes with GitHub Copilot
- Submit a PR from a working branch (use this submission process in later sessions too)

## What to Prepare

- A personal GitHub account (accounts managed by a company may have Codespaces or Copilot disabled by organization settings)
- A personal Google account (company Google Workspace accounts may have AI Studio disabled by administrator settings)

## Exercises (45 Minutes)

### 1. Fork the Course Repository

Use **Fork** at the top right of the course repository to create a fork under your account. Do all subsequent work in your own fork.

### 2. Create a Gemini API Key

Create and copy an API key in [Google AI Studio](https://aistudio.google.com/apikey).

> API keys are secrets. Do not paste them into code, chat, or commits. If a key leaks, delete it in AI Studio and create a new one.

### 3. Register It as a Codespaces Secret

Under GitHub **Settings → Codespaces → Secrets → New secret**, register:

- Name: `GEMINI_API_KEY`
- Value: the key from step 2
- Repository access: select **your own fork**

> Register the secret before starting Codespaces. If you register it after startup, restart your Codespace.

### 4. Start Codespaces

In your fork, select **Code → Codespaces → Create codespace on main**. Preparing the environment takes a few minutes the first time. Run the following in the terminal and check that the tests pass.

```bash
uv run pytest -q
```

### 5. Ask a Bare LLM

```bash
uv run python -m app.ask "What is LoRA?"
uv run python -m app.ask "What are the 3 homework levels in the AIE2026 course?"
```

The first question asks about a general term, so the answer should be broadly correct. The second asks about the course-specific "3 homework levels". A bare LLM does not know about this course, so it may say "I don't know" or give a plausible answer based on general knowledge. The correct information is in `homework-levels` in `data/glossary.json`. Compare it with the model's answer.

If you have time, try other course-specific questions. Notice that the same question can produce different answers on different runs, and that the model may answer confidently even when it does not know.

```bash
uv run python -m app.ask "What is a lecNN-start tag in the AIE2026 course?"
uv run python -m app.ask "What will we learn in Lecture 02 of AIE2026?"
```

### 6. Use Copilot to Display Token Counts

At `TODO(Lecture 01 exercise)` in `app/ask.py`, modify the code to display input and output token counts. You may use Copilot completion or chat. Read and understand suggested code before accepting it.

### 7. Create a Branch and Open a PR

```bash
git switch -c lec01
# Fill in lectures/01/answer.md
git add -A
git commit -m "Lecture 01 exercises"
git push -u origin lec01
```

On GitHub, create a PR from `lec01` to `main` in your own fork. **Check that the base repository is your own fork** (do not open a PR against the course repository).

### 8. Stop Codespaces

Select "Codespaces" at the bottom left → **Stop Current Codespace**. Leaving it running continues to consume your free allowance.

## Homework (Complete Any One Level)

| Level | Task |
|---|---|
| Basic | Run each question three times, using different models (the `AIE_MODEL` environment variable) or different temperature values, and summarize the differences in answer.md |
| Implementation | Modify `app/ask.py` to support follow-up questions while retaining conversation history |
| Advanced | Measure response time and token counts, and compare multiple models or questions. Discuss their relationship to the free-tier rate limits |

Example of switching models:

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "What is LoRA?"
```

### Additional Notes on the Model You Call

Model specifications may change.
The Gemini API documentation has been updated: Gemini 3.5 Flash is now deprecated and redirects to Gemini 3.6 Flash.

- Reference: Gemini 3.5 Flash documentation
https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash?hl=en

As this example shows, the specifications of LLMs provided as services change frequently. Make a habit of checking the service documentation so that you can adapt to specification changes.

For the Lecture 01 homework, you may use any model of your choice.

To change temperature, look up the `config` argument of `generate_content`.
