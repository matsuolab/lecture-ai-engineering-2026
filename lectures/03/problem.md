# Lecture 03 Exercises and Homework: Build a Learning Support Agent

## Goals for This Session

- Verify in your own code that an agent consists of "model + loop + tools"
- Read which tools were called with which arguments
- Add one tool

## Exercises (30 Minutes)

We will spend approximately the first five minutes explaining the Lecture 02 homework. During that time, click Sync fork in step 1 and start Codespaces (startup takes a few minutes).

### 1. Sync Updates from the Course Repository and Create the lec03 Branch

Bring the course repository's updates into your own fork before creating a working branch.

1. Open your fork on GitHub and select **Sync fork → Update branch** (if it is already up to date, Update branch will not appear, and you do not need to do anything)
2. Start Codespaces and run the following commands in the terminal

```bash
git switch main
git pull --no-rebase
git switch -c lec03
```

- If `git switch main` stops, you have uncommitted changes on the previous session's branch. Commit them on that branch, then try again
- If you see `a branch named 'lec03' already exists`, you have already created `lec03`. Switch to it with `git switch lec03`
- If `git pull --no-rebase` reports `CONFLICT`, run `git merge --abort` to return to the previous state, then use the alternative below (aborting the merge preserves your own changes)

#### If main Is Broken or You Have Not Finished the Previous Sessions

If Sync fork displays a conflict prompt (creating a pull request or "Discard commits"), **do not select it**; start with the method below instead. Selecting "Discard commits" deletes your own commits.

Create a branch from the course repository's starting code (the `lec03-start` tag).

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec03-start
git switch -c lec03 lec03-start
```

### 2. Ask the Agent the Same Question as in Lecture 01

```bash
uv run python -m app.agent "What are the 3 homework levels in the AIE2026 course?"
```

Compare the answer with `app.ask` in Lecture 01. The agent searches the glossary before answering. The correct information is in the `homework-levels` entry of `data/glossary.json`.

### 3. Read Tool Calls

```bash
uv run python -m app.agent --trace "What is the difference between LoRA and QLoRA?"
```

On the `[tool call]` lines, check which tools the model called with which arguments. `requests` in `[usage]` shows how many LLM calls were made for one question.

The instructions explain why the model should search before answering and look up one term at a time. They are in two places:

- `INSTRUCTIONS` in `app/agent.py` (around line 31): instructions for the whole agent, such as "Always check the glossary with search_glossary" and "End your answer by indicating the relevant session (Lecture NN)"
- Each tool's docstring in `app/tools.py`: passed to the model as the tool description. The docstring of `search_glossary` says to put only one term to look up in `query`

For the Basic homework, rewrite these instructions and compare how the agent's behavior changes.

### 4. Write and Register the make_quiz Tool

Enable the agent to create a question from the glossary when asked for a review question from Lecture 02. The model calls `make_quiz` with `lecture=2`; the tool chooses one term from Lecture 02 and returns a question and answer, which the model uses to pose the question.

1. Add a function `make_quiz(lecture: int) -> str` to `app/tools.py`
2. Write a docstring explaining when and why to use the tool (the model reads it to decide whether to use the tool)
3. From the glossary (`load_glossary()`), collect terms whose `lecture` matches the requested session and choose one (for example, with `random.choice`)
4. Return a string containing a question such as "What does this term mean?" and its answer (the term's `definition`), for example using `json.dumps`
5. Register it with `agent.tool_plain(tools.make_quiz)` at `TODO(Lecture 03 exercise)` in `app/agent.py`

Example return value of `make_quiz(2)`:

```text
{"question": "What does PEFT mean?", "answer": "Rather than all of the model's parameters, …"}
```

### 5. Check That make_quiz Is Called

```bash
uv run python -m app.agent --list-tools    # List tools visible to the model (no API key needed)
uv run python -m app.agent --trace "Give me one review question from Lecture 02"
uv run pytest -q
```

You have succeeded if the list includes `make_quiz` and your docstring, and you see a line such as `[tool call] make_quiz({'lecture': 2})`.

Without using an API key, `uv run pytest -q` calls all tools, including the `make_quiz` you added, with dummy arguments (such as `lecture=0`) to check that they do not fail with an error. Lecture 0 does not exist, so the test fails if you have not handled the case where no terms are found. In that case, make the tool return a clear message when no terms exist.

- Missing from the list → it has not been registered in `app/agent.py`
- Listed but not called → describe a specific use case in the docstring. Add an instruction such as "Use make_quiz when asked for a review question" to `INSTRUCTIONS`

### 6. Submit and Stop Codespaces

Fill in `lectures/03/answer.md` and open a PR from `lec03` to `main` in your own fork. **Check that the base repository is your own fork.**

```bash
git add -A
git commit -m "Lecture 03 exercises"
git push -u origin lec03
```

If you did not finish step 4, you may submit the results through step 3. Push further work to the same branch to update the PR.

Finally, select "Codespaces" at the bottom left → **Stop Current Codespace**.

## Homework (Complete Any One Level)

Choose one of the three levels: Basic, Implementation, or Advanced. Working on any one level completes the homework.

| Level | Task |
|---|---|
| Basic | Rewrite `INSTRUCTIONS` in `app/agent.py` or tool docstrings in `app/tools.py`, as examined in the exercises. Run the same question with `--trace`, then compare and record how the tool calls and answers change |
| Implementation | Create a `save_learning_log` tool that saves learning records in `learning_log/`. Since saving is difficult to undo, ask the user for confirmation before saving (Pydantic AI's `requires_approval=True`) |
| Advanced | Choose one: (a) Keep the same instructions and tools as the exercise agent, rewrite only the agent assembly using Google's ADK, run it with `adk run`, and compare the code and answers. (b) Run the coding agent Pi in Codespaces and compare its public system prompt with your own agent's `INSTRUCTIONS` |

Submit your work in the "Homework" section of the same `lectures/03/answer.md` used for the exercises.

### How to Approach the Basic Level

Change only one of the two instruction locations from exercise step 3 at a time. Run the same question with `--trace` and compare the results.

- `INSTRUCTIONS` in `app/agent.py` (around line 31): instructions for the whole agent
- Each tool's docstring in `app/tools.py`: passed to the model as the tool description

For example, try the following changes. Record how the selected tools, number of calls, arguments, and answers change.

- If you remove the instruction to always check the glossary with `search_glossary` from `INSTRUCTIONS`, does the agent answer without searching?
- If you change the `search_glossary` docstring from "Put only one term to look up in query" to "Put several terms together", how do the number of searches and arguments change?
- If you replace "End your answer by indicating the relevant session (Lecture NN)" in `INSTRUCTIONS` with another instruction (such as "End with one review question"), how does the answer change?

### How to Approach the Implementation Level

1. Create `save_learning_log` in `app/tools.py` and register it in `app/agent.py` with `requires_approval=True`
2. When the model calls this tool, execution pauses for approval and returns `DeferredToolRequests` as the result (`result.output`). Add `DeferredToolRequests` to the agent's `output_type` (otherwise an error occurs)

   ```python
   from pydantic_ai import Agent, DeferredToolRequests

   agent = Agent(instructions=INSTRUCTIONS,
                 output_type=[str, DeferredToolRequests])
   ```

3. In the CLI, ask the user whether saving is allowed for each call in `result.output.approvals`. Pass those decisions (`DeferredToolResults`) and the conversation so far (`message_history=result.all_messages()`) to another call to `run_sync`

For details, refer to Human-in-the-Loop Tool Approval in the official Pydantic AI "Deferred Tools" documentation: https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/

### How to Approach Advanced Option (a): Rebuild with ADK

Keep the exercise agent's instructions and tools, and rewrite only the agent assembly using ADK.

| Scope | Details |
|---|---|
| Reuse | `INSTRUCTIONS` from `app/agent.py`, and `search_glossary` and `get_lecture_summary` from `app/tools.py` (also `make_quiz` if you created it during the exercises) |
| Write | Create `agent.py` (the code below) and `__init__.py` (the single line `from . import agent`) in `adk_agent/glossary_agent/` |
| Not required | Command features such as `--trace`, tests, or tools requiring approval. Leave the files in `app/` unchanged |
| Compare | The code (how instructions and tools are passed) and differences in answers to the same questions used in the exercises |

Structure of `adk_agent/glossary_agent/agent.py`:

```python
from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[...],  # Tools used in the exercises
)
```

Run the following command from the repository root:

```bash
PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
```

- `adk run` provides a terminal conversation. Type a question and press Enter to receive an answer. Type `exit` to finish
- `uv run --with google-adk` temporarily adds ADK to the course environment for this run. It does not change `pyproject.toml` or `uv.lock`
- `PYTHONPATH=.` is needed to import the `app` folder from the repository root
- The API key comes from the existing Codespaces secret `GEMINI_API_KEY`
- Downloading ADK takes about one minute on the first run

Ask the same questions as in the exercises, and record differences in the code and answers compared with the Pydantic AI version.

ADK 2.0 introduced major changes. Articles on the web may contain outdated information that does not account for these changes, so following the official documentation should help avoid implementation mistakes.

- Official documentation: https://adk.dev/

### How to Approach Advanced Option (b): Run Pi in Codespaces

Pi is a coding agent that edits files and runs commands without requesting confirmation. Try it inside Codespaces rather than on your own PC.

1. **Install**: run the following in the Codespaces terminal

   ```bash
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

2. **Start**: type `pi` in the terminal
3. **Configure the model**: type `/model` inside Pi and select a Gemini model. The existing Codespaces secret `GEMINI_API_KEY` supplies the API key
4. **Compare**: Pi's system prompt is in `packages/coding-agent/src/core/system-prompt.ts` in the public repository https://github.com/earendil-works/pi. Compare it with your `INSTRUCTIONS` to see what is included and omitted

- Official Pi documentation: https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## References

- Pydantic AI: https://pydantic.dev/docs/ai/
- ADK: https://adk.dev/
