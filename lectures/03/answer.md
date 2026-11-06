# Answer to Question 3

## Exercise

- **Differences between the first round (raw LLM) and the agent's responses:** 
  The raw LLM relies solely on internal parameters, whereas the agent dynamically calls external tools (`search_glossary`, `make_quiz`) to retrieve accurate, domain-specific course knowledge.
- **Tool calls (tool name and arguments) seen with `--trace`:** 
  `make_quiz({'lecture': 2})` and `search_glossary({'query': 'LoRA'})` / `search_glossary({'query': 'QLoRA'})` were correctly invoked and traced.
- **Number of LLM calls in a single question (`requests`):** 
  Typically 2 requests per query as the agent processes the prompt, calls the tool, receives the tool return, and formulates the final response.
- **Added tools and their descriptions in the docstring:** 
  Added the `make_quiz` tool to `app/tools.py` with clear docstrings describing its purpose, allowing the model to determine when and how to generate review quizzes for specified lectures.

## homework

- **Levels worked:** Basic / Implementation / Advanced
- **Things I did:**
  - **Basic:** Modified instructions and tested how altering prompt constraints affects tool usage behavior using `--trace`.
  - **Implementation:** Created the `save_learning_log` tool in `app/tools.py` and set up human-in-the-loop approval (`requires_approval=True`, `output_type=[str, DeferredToolRequests]`) in `app/agent.py`. Adjusted assertions in `tests/test_agent.py` to handle deferred tool requests.
  - **Advanced:** Installed and launched the `pi` coding agent in Codespaces (`@earendil-works/pi-coding-agent`), exploring its automated workflow and comparing its core system prompt with custom agent instructions.
- **Result:** 
  - All test suites passed successfully (`uv run pytest -q` -> 11 passed).
  - Successfully verified tool tracing, human-in-the-loop approvals, and coding agent workflows.
- **Observations and questions:** 
  - Implementing `requires_approval=True` brilliantly demonstrates how critical actions (like file writing) can be paused safely. Adapting test suites for deferred states provides valuable insights into agent control flow.