# Lecture 03 Answers

## Exercises

- Differences between the Lecture 01 (bare LLM) and agent answers:
  The bare model did not know the AIE2026 course and named no homework levels. The agent looked it up and answered correctly: Basic, Implementation, Advanced. It also ended with the lecture number (Lecture 01).
- Tool calls shown by `--trace` (tool names and arguments):
  - LoRA vs QLoRA: `search_glossary({'query': 'LoRA'})` and `search_glossary({'query': 'QLoRA'})`
  - Review question: `make_quiz({'lecture': 2})`
- Number of LLM calls for one question (`requests`):
  2 (one to choose the tools, one to write the answer).
- Tool added and the description in its docstring:
  `make_quiz(lecture)` picks one term from the lecture and returns a question and its answer. The docstring says to use it when the learner asks for a review question, not to use it to explain a term, and to show only the question first.

## Homework

- Level attempted: Basic, Implementation, Advanced
- What you did:
  - Basic: changed the `search_glossary` docstring and compared the same question with `--trace`.
  - Implementation: added `save_learning_log` with `requires_approval=True`, so the user must approve before it writes.
  - Advanced: rebuilt the agent with Google ADK, keeping the same instructions and tools.
- Results:
  - Basic: with "only one term", the model made 2 searches (input tokens 1129). With "several terms", it made 1 search (input tokens 836).
  - Implementation: with a strict docstring the model never called the tool. After loosening the wording it called the tool, asked for approval, and saved the note after I typed `y`.
  - Advanced: ADK gave the same single tool call and the same style of answer as the first framework. Only one run was tested.
- Observations and questions:
  The docstring decides whether a tool is called and how many times. A small wording change gave a different result, so tool descriptions need to be written carefully.

