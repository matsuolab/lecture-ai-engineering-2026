# Lecture 03 Homework Results

Agent: model `gemini-3.5-flash-lite`, Python 3.12.7. Basic and implementation levels use Pydantic AI v2.57.0; the advanced level rebuilds the same agent with Google ADK.

| Level | Experiment | What it covers |
|---|---|---|
| Basic | 1. Docstring wording | How tool descriptions change the number of searches |
| Implementation | 2. `save_learning_log` | A new tool that writes to disk, with human approval |
| Advanced | 3. Rebuild with Google ADK | Same instructions and tools, different framework |

---

## Basic level: Experiment 1, docstring wording and the number of searches

Question (same every run): `What is the difference between LoRA and QLoRA?`

| Run | `search_glossary` docstring | Calls | `query` arguments | Input tokens | Output tokens | Cost |
|---|---|---|---|---|---|---|
| 1 | Original (only one term per query) | 2 | `'LoRA'`, `'QLoRA'` | 1129 | 311 | $0.0011162 |
| 2 | First instruction line removed | 2 | `'LoRA'`, `'QLoRA'` | 1087 | 260 | $0.0009761 |
| 3 | "Put several terms" | 1 | `'LoRA QLoRA'` | 836 | 277 | $0.0009433 |

### Observations

- Run 2 behaved the same as run 1. Removing that line did not change tool use.
- Run 3 cut the calls from 2 to 1 and input tokens from 1129 to 836. The model combined both terms into a single query, as the new wording invited.
- `requests=2` in every run, so the model still made two requests. The saving came from fewer tool calls and results, not from fewer model round trips.
- The combined query `'LoRA QLoRA'` only worked because of the function's substring matching: `_normalize` turns it into `loraqlora`, which matches no entry exactly, but the partial-match rule (`n in q`) finds both `lora` and `qlora` inside it. This is fragile.
- Risks of multi-term queries: the `MAX_RESULTS = 3` cap, names under 3 characters being skipped, and no per-term "not found" message.
- Each condition ran once. Differences in answer wording are ordinary model variation, so only the tool-call counts are reliable.

### Takeaway

Changing "only one term" to "several terms" reduced searches from 2 to 1, but a docstring change should be matched by the function behind it. To support several terms reliably, split the query on commas inside `search_glossary` and report "not found" per term.

---

## Implementation level: Experiment 2, `save_learning_log` with `requires_approval=True`

Setup:
- Tool added to `app/tools.py`, registered with `agent.tool_plain(tools.save_learning_log, requires_approval=True)`.
- `output_type=[str, DeferredToolRequests]` set on the agent (banner shows `output: str | DeferredToolRequests`, `tools: 3`).
- Approval loop added in `main()`.

| Docstring wording | Question | Tool called? | Approval prompt? | Result |
|---|---|---|---|---|
| Strict ("use ONLY when the user explicitly asks") | `What is LoRA? Then save a note about it to my learning log.` | No | No | Model answered, then said it would save only if explicitly asked |
| Loosened (includes phrases like "save a note about it") | Same question | Yes | Yes | Approved with `y`; tool returned `Saved to learning log: ...` |

Trace of the successful run:

```
[tool call]   search_glossary({'query': 'LoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, ...
[approval needed] save_learning_log({'summary': 'LoRA freezes base weights and trains low-rank adapter matrices to adapt models efficiently with fewer trainable parameters (Lecture 02).'})
Approve? [y/N] y
[tool call]   save_learning_log({'summary': '...(Lecture 02).'})
[tool return] save_learning_log -> Saved to learning log: LoRA freezes base weights ...
[usage] requests=1, tool_calls=1, cost=$0.0006068
```

### Observations

- The approval pause works: the run stopped before any file was written, and resumed after `y`.
- The docstring controlled whether the tool was called at all. The strict version was too cautious, and the loosened one worked.
- The final answer did not mention that the note was saved. A line in `INSTRUCTIONS` asking the agent to confirm saves would fix that.
- The `[usage]` line covers only the resumed run (`requests=1`), so the true cost is higher than printed.

### Still to verify

- [ ] `data/learning_log.md` contains the saved line
- [ ] Answering `n` writes nothing and the agent does not claim it saved
- [ ] `What is LoRA?` alone triggers no approval prompt (run 2 or 3 times)

---

## Advanced level: Experiment 3, the same agent rebuilt with Google ADK

Goal: keep the same `INSTRUCTIONS` and the same tools from `app/tools.py`, and rewrite only the agent-building part and the run loop with Google's Agent Development Kit (ADK).

### Code comparison

| | Pydantic AI | Google ADK |
|---|---|---|
| Create the agent | `Agent(instructions=INSTRUCTIONS, output_type=[str, DeferredToolRequests])` | `Agent(name=, model=, description=, instruction=, tools=[...])` |
| Model | Passed at run time: `run_sync(q, model=...)` | Passed in the constructor |
| Register tools | `agent.tool_plain(fn)` per tool | `tools=[...]` list; plain functions work directly |
| Tool descriptions | Docstring and type hints | Docstring and type hints (same) |
| Approval for `save_learning_log` | `requires_approval=True` plus a `DeferredToolRequests` loop in `main()` | `before_tool_callback` that asks `Approve? [y/N]` in the terminal |
| Running it | `agent.run_sync(...)` | `InMemoryRunner` with `run_async(...)`, streaming events |
| Trace | `print_trace(result)` reads the message history | Built from `get_function_calls()` and `get_function_responses()` on each event |
| Usage and cost | `[usage]` line with tokens and cost | Not printed in this version |
| API key | `GoogleProvider(api_key=get_api_key())` | Copied into the `GOOGLE_API_KEY` environment variable |

Problems met along the way:
- `ModuleNotFoundError: No module named 'google.adk'` until `uv add google-adk` was run.
- `AttributeError: 'LlmAgent' object has no attribute 'run_sync'`. After the agent definition was swapped to ADK, `main()` still called Pydantic AI's `run_sync`. ADK needs its own runner, so the run path had to change too, not just the agent definition.
- Using `require_confirmation=True` would have required `main()` to send a confirmation event back to the runner. A `before_tool_callback` was simpler.
- Both frameworks export a class named `Agent`. Importing both under the same name makes one silently replace the other.

### Answer comparison

Question: `What is the difference between LoRA and QLoRA?`

| | Pydantic AI (run 3) | Google ADK |
|---|---|---|
| Tool calls | 1 | 1 |
| `query` argument | `'LoRA QLoRA'` | `'LoRA QLoRA'` |
| Ends with Lecture NN | Yes, `(Lecture 02)` | Yes, `(Lecture 02)` |
| Closing hint question instead of a full homework answer | Yes | Yes |

ADK trace:

```
[tool call]   search_glossary({'query': 'LoRA QLoRA'})
[tool return] search_glossary -> {'result': '[{"term": "LoRA", "lecture": 2, "definition": "A PEFT method that freezes pretrained weights, represents wei…
```

### Observations

- The ADK agent made the same single combined tool call as the Pydantic AI run with the "several terms" docstring, and followed the same `INSTRUCTIONS` rules (ends with the lecture number, guides with a hint).
- ADK wraps the tool's return value in a dictionary (`{'result': ...}`), while Pydantic AI showed the raw string. The tool itself is unchanged.
- The ADK agent file is shorter at the agent-building step, because the runner supplies the loop. The cost is that the trace, approval and token reporting must be written by hand, and `--list-tools` and `--mcp` from the Pydantic AI version do not carry over.
- Only one question was run on ADK, once. Matching tool calls on a single run are not strong evidence. Answer wording differs from run to run in any framework.


---

## Summary

**Basic:** Tool docstrings decide whether a tool is called and what arguments the model passes. Changing "only one term" to "several terms" cut searches from 2 to 1 and input tokens from 1129 to 836, but it leans on fragile substring matching in the function.

**Implementation:** For a tool that writes to disk, the wording had to be loosened enough for the model to call it, and `requires_approval=True` gives a human check before anything is written.

**Advanced:** Rebuilding the agent with Google ADK kept the same instructions, tools and docstrings, and the first test gave the same tool call and answer style. The main differences are who owns the run loop, where the model is set, and how approval is handled. Swapping only the agent definition is not enough, because the runner has to change too.

One rule to keep: state when to use a tool, when not to, and the exact argument format, and make sure the function behind it handles what the description invites.
