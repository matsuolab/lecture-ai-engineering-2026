# AIE2026 Exercises and Homework Repository

This repository is used for exercises and homework in the AI Engineering Pilot Course (AIE2026).
Throughout the course, you will gradually develop an **agent that supports learning AI engineering**.

## Expected Environment

The exercises are designed to run **entirely in a browser**. You do not need to install anything on your own PC.

| What you need | Purpose | Notes |
|---|---|---|
| A **personal** GitHub account | Fork this repository and submit work through a working branch and PR | Accounts managed by a company or school may restrict Codespaces and Copilot |
| GitHub Codespaces | Development environment for Lecture 01, Lecture 03, Lecture 05, and other sessions. The configuration in `.devcontainer/` automatically prepares a container with Python 3.12, uv, and Node.js | Personal accounts have a free allowance of 120 core-hours per month (about 60 hours with 2 cores). **Stop your Codespace when you finish** |
| GitHub Copilot (Free is sufficient) | Code completion and chat. Also used as an MCP client in the Lecture 06 advanced homework | Free has monthly limits on completions and chat usage |
| Gemini API (Google AI Studio free tier) | Call the LLM. Create a key with a **personal** Google account and pass it through the Codespaces secret `GEMINI_API_KEY` | The free tier has per-minute and daily limits (see "Assumptions and Constraints" below) |
| Google Colab (T4 GPU, free tier) | Used only for LoRA training in Lecture 02 | GPU usage time is limited. Disconnect and delete the runtime when you finish |

To run locally on your own PC, install Python 3.12 and [uv](https://docs.astral.sh/uv/), run `uv sync --frozen`, and set the `GEMINI_API_KEY` environment variable.

## Getting Started (Lecture 01)

1. **Fork** this repository to your own account
2. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey)
3. Register `GEMINI_API_KEY` under GitHub **Settings → Codespaces → Secrets**, and select your own fork for repository access
4. In your fork, select **Code → Codespaces → Create codespace on main**
5. Check that everything works in the terminal

```bash
uv run pytest -q
uv run python -m app.ask "What is LoRA?"
```

See [lectures/01/problem.md](lectures/01/problem.md) for detailed instructions.

## Structure

```
.devcontainer/   Codespaces environment definition (Python 3.12, uv, Node.js; runs uv sync --frozen on startup)
.github/workflows/test.yml  Runs tests for each PR (enable workflows in the Actions tab in your fork)
app/
  config.py      Loads the model name and API key
  ask.py         Lecture 01: ask the LLM a question
  tools.py       Lecture 03: agent tools (glossary search, etc.)
  agent.py       Lecture 03: Pydantic AI learning support agent (Lecture 06: through MCP with --mcp)
  judge.py       Lecture 04: grade the evaluation set with an LLM and report agreement with human labels
  mcp_server.py  Lecture 06: MCP server that exposes the glossary
  mcp_servers.json Lecture 06: configuration of MCP servers to use (mcpServers format)
data/
  glossary.json  Course glossary
  lectures/      Key points from each session
  eval/          Lecture 04: evaluation set (lec04_cases.jsonl) and grading rubric (rubric.md)
tools/
  annotate.py    Lecture 04: interface for labeling the evaluation set (Streamlit; temporarily added with uv run --with)
.streamlit/      Streamlit configuration for access through Codespaces port forwarding
lectures/NN/
  problem.md     Exercises and homework for that session
  answer.md      File for you to fill in and submit
notebooks/       Lecture 02: LoRA notebook for Google Colab (lora_format_tuning.ipynb)
scripts/         Helper scripts
tests/           Tests (no API key required)
pyproject.toml / uv.lock  Dependencies and their pinned versions
```

## How to Submit

1. Create a working branch for each session (for example, `git switch -c lec01`)
2. Complete the exercises and homework, and fill in `lectures/NN/answer.md`
3. Push, then create a PR from your working branch to `main` **within your own fork**

Homework has three levels: "Basic", "Implementation", and "Advanced". Completing any one level is sufficient.

## Assumptions and Constraints

- **Dependency versions are pinned** (`uv.lock`: Python 3.12, pydantic-ai-slim 2.57.0, google-genai 2.31.0). We will not upgrade them during the course. Install them as provided with `uv sync --frozen`.
- **The default model is `gemini-3.5-flash-lite`**. Change it with the `AIE_MODEL` environment variable (see "Switching Models" below). You may also use other models or your own API subscription
- **The Gemini API free tier has rate limits**. Agents (Lecture 03 onward) call the LLM multiple times for one question, so they reach the limit sooner than in Lecture 01. If you see `Rate limit reached`, wait about 1 minute. If `The model is busy (503)` keeps appearing, try `AIE_MODEL=gemini-3.1-flash-lite`
- **Pass the API key only through the `GEMINI_API_KEY` environment variable**. Do not paste it into code, commits, or chat. If it leaks, delete it in AI Studio and create a new one
- Codespaces can access the internet, but outside connections cannot enter your Codespace (forwarded ports are private by default). Run the Lecture 06 MCP server inside Codespaces
- Tests (`uv run pytest -q`) run without an API key (they use TestModel, which does not call an LLM)

## Rules to Follow

- **Do not put API keys in code or commits.** Pass them through Codespaces secrets
- **Stop Codespaces when you finish.** You cannot start a Codespace after exhausting the free allowance
- You may use AI tools such as Copilot. Read and understand suggested code before accepting it

## Switching Models

The default model is `gemini-3.5-flash-lite`. Change it with the `AIE_MODEL` environment variable.

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "What is LoRA?"
```

The free tier has per-minute and daily request limits. See the [Gemini API rate limits page](https://ai.google.dev/gemini-api/docs/rate-limits) for the limits.
