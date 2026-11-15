# Lecture 05 Exercises and Homework: Answer Questions by Searching Lecture Materials

**Release status:** These translated instructions and the answer template are available for review. The localized lecture materials, search index, and Lecture 05 runtime activation are pending. The exercise commands below are for use after the data and code update is released.

## Goals for This Session

- Run full-context and retrieval-based answering, and compare answers, evidence, time, and token counts
- Explain the data representation with one page per chunk and the differences between vector search, Tree, and Graph retrieval
- Improve retrieval for your own use case and compare before and after using the same question

Use Lecture 03's "model + loop + tools" structure while changing how lecture materials are retrieved. Building on Lecture 04's evaluation work, check answer correctness and the evidence in cited pages yourself.

## Materials and Code

The four data links below point to the original Japanese reference data at a fixed revision; localized files are pending. The code links point to prepared English code on the preparation branch, pending activation in `main`.

| File | Contents |
|---|---|
| [data/rag_data/lectures.json](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/1ce722c2816b70ef62891a6378b2478af555e3fd/data/rag_data/lectures.json) | Titles and text organized by lecture, section, and page. One page is used as one chunk |
| [data/rag_data/tree.json](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/1ce722c2816b70ef62891a6378b2478af555e3fd/data/rag_data/tree.json) | Document, section, and page hierarchy |
| [data/rag_data/graph.json](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/1ce722c2816b70ef62891a6378b2478af555e3fd/data/rag_data/graph.json) | Nodes such as pages and terms, and the relationships connecting them |
| [data/rag_data/index.sqlite3](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/1ce722c2816b70ef62891a6378b2478af555e3fd/data/rag_data/index.sqlite3) | Search database containing 214 pages from the main materials for Lectures 01–03 |
| [scripts/build_rag_index.py](https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/feat/lecture05-rag-update-20261115/scripts/build_rag_index.py) | Embeds materials and creates a SQLite search database |
| [app/retrieval.py](https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/feat/lecture05-rag-update-20261115/app/retrieval.py) | Vector search, Tree traversal, Graph traversal, and full-context processing |
| [app/tools.py](https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/feat/lecture05-rag-update-20261115/app/tools.py) | Descriptions, inputs, and outputs of the tools available to the model |
| [app/agent.py](https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/feat/lecture05-rag-update-20261115/app/agent.py) | Instructions, tool registration, and mode selection |
| [app/config.py](https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/feat/lecture05-rag-update-20261115/app/config.py) | Settings such as target materials, result counts, and Graph traversal limits |

**Scope of the prepared exercise**: Vector search, Tree, and Graph are designed to use 214 pages from the main materials for Lectures 01–03. Full context uses all 9 documents and 438 pages in the materials JSON. This exercise explores different retrieval paths. To compare the methods under the same conditions, first align their target materials.

## Preparation

### 1. Get the Lecture 05 Update and Create the lec05 Branch

After the Lecture 05 data and runtime update is published in the course repository, select **Sync fork → Update branch** in your fork, then run these commands in the Codespaces terminal:

```bash
git switch main
git pull --no-rebase
git switch -c lec05
uv sync --frozen
```

- If `lec05` already exists, switch to it with `git switch lec05`
- If changes from the previous session prevent switching branches, commit them on that branch and retry
- If conflicts occur during the update, consult the instructor without discarding your changes

Use the same `GEMINI_API_KEY` environment variable as in Lecture 01. If you added the Codespaces secret after startup, restart Codespaces. See the [README](../../README.md) for setup instructions.

### 2. Check the Search Database After the Data and Runtime Update

Before starting, confirm that the data and runtime update supplies the lecture materials and `data/rag_data/index.sqlite3`. Vector search and Graph use that database as provided. These prerequisites are pending in the current release. Query embedding and answer generation use `GEMINI_API_KEY`. Tree and full context do not need the search database, but still require the materials and updated code.

## Exercises

### STEP 1: Pass All Materials at Once and Generate an Answer

First, store the comparison question in a variable in the same terminal. Use this question unchanged for each method below.

```bash
AIE_QUESTION='In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?'
uv run python -m app.agent --full-context --trace "$AIE_QUESTION"
```

Record the answer, cited pages, and the final `[time]`, `[usage]`, and `[cost]` values in [answer.md](answer.md).

Full context can also answer correctly. Examine the actual result without assuming failure. Record input-limit errors separately from cases where the input is accepted but the necessary evidence is not used.

### STEP 2: Inspect the Search Results Alone

```bash
uv run python -m app.retrieval "LoRA QLoRA difference"
```

This retrieves up to 5 pages similar to the question without using an agent. It displays the lecture name, section, page title, PDF page number, and text.

- Do the results include pages supporting an answer, such as Lecture 02 / PDF p.52?
- Can you distinguish pages that merely contain similar terms from pages that provide evidence for the answer?

Open the materials JSON in the editor and search for a page ID, such as `lec02-main-p052`, to inspect that page's text.

### STEP 3: Generate an Answer Using Search Results

```bash
uv run python -m app.agent --trace "$AIE_QUESTION"
```

By default, the agent answers using its `search_materials(query)` tool. The model chooses the search terms and answers from the returned text.

- Check the search terms and number of tool calls in `[tool call]`
- Check whether each "Lecture N / PDF p.N" citation supports the explanation
- Distinguish failure to retrieve the evidence from failure to use retrieved evidence correctly

For some questions, p.52 alone provides all the evidence needed. Increasing the number of cited pages is not a goal in itself.

### STEP 4: Answer the Same Question with Tree and Graph

Tree selects pages by following the table of contents.

```bash
uv run python -m app.agent --tree --trace "$AIE_QUESTION"
```

It uses only `browse_tree(node_id)`. The first call retrieves a lecture list; subsequent calls use the returned IDs to navigate to lectures, sections, and pages. Page entries in `children` contain only the first sentence; specifying a page ID returns its full text in `node.content`. For a page without sentence-ending punctuation, the preview is its first line. Use the trace to inspect the table-of-contents choices and the pages whose full text was retrieved.

Graph finds starting points through vector search and expands to nearby candidates.

```bash
uv run python -m app.agent --graph --trace "$AIE_QUESTION"
```

It uses `search_graph(query)`. Starting from the top 3 search results, it follows relationships through adjacent pages and shared terms for up to 2 hops, returning text from up to 10 pages including the starting points. Moving from a page to an adjacent page is 1 hop; moving from a page through a term to another page is 2 hops. Shared terms do not guarantee that a page contains the answer.

Record how Tree and Graph affect the answer, cited evidence, time, and input token count.

### STEP 5: Compare and Record Results

Summarize each method's results in the table in `answer.md`.

| Output | Meaning |
|---|---|
| `[time]` | Seconds until the answer is complete, including retrieval and embedding |
| `[usage]` | Total input and output tokens and model responses for one question |
| `[cost]` | Estimated generation API cost. Excludes query embedding and index construction |

If the cost is "Unavailable", record that as shown; do not treat it as zero.

If you have time, repeat the comparison with a different question. Keep separate results for each question when reporting several.

| Type | Example question | Evidence to check |
|---|---|---|
| Multiple pages | In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory? | Lecture 03 / PDF p.13, 39, 40 |
| Absent from the materials | What are the measured average response time and accuracy of the RAG system we just built? | The lecture materials contain no measurement logs for this system |

### STEP 6: Submit and Stop Codespaces

Write the exercise results in `lectures/05/answer.md` and open a PR from your working branch to `main` in your own fork. **Check that the base repository is your own fork.**

```bash
git add lectures/05/answer.md
# If you changed code, git add those files too
git commit -m "Lecture 05 exercises and homework"
git push -u origin lec05
```

Keep API keys and experimental search databases out of commits. Finally, select "Codespaces" at the bottom left → **Stop Current Codespace**.

## Homework (Complete Any One Level)

Choose Basic, Implementation, or Advanced. **Completing any one level is sufficient.** In the "Homework" section of the same `answer.md`, record your level, what you did, results, and observations or questions.

| Level | Task |
|---|---|
| Basic | Change one instruction, tool description, or search result count. Run the same question with `--trace` and compare before and after |
| Implementation | Improve one part of retrieval, such as including the text of adjacent pages with search results, and compare it with normal retrieval |
| Advanced | Improve Tree, Graph, or a combination of methods. Choose a question to solve and compare with basic RAG using the same question |

### How to Approach the Basic Level

Change only one of the following at a time:

- `INSTRUCTIONS` in `app/agent.py`, or `TREE_INSTRUCTIONS` / `GRAPH_INSTRUCTIONS` when using Tree / Graph
- A tool's docstring in `app/tools.py`
- `RAG_TOP_K` in `app/config.py` (the number of results returned by normal vector search)

Use the same question, model, and materials to check changes in tool selection, arguments, and call counts, as well as the answer and cited evidence. Record time, token counts, and estimated generation API cost too. These changes alone do not require rebuilding the index.

### How to Approach the Implementation Level

For example, modify `app/retrieval.py` to return the text of the page immediately before and after each retrieved page.

1. Use the page metadata from `load_pages()` to find adjacent pages within the same `document_id` as the search result
2. Avoid returning duplicate pages, and include both text and citation metadata
3. Run the same question as before the change. Identify examples where necessary evidence was added and examples where unnecessary information increased
4. Record your implementation, comparison results, and remaining failures

You may instead improve retrieval in another way suited to your use case. Changing only the retrieval range, without changing the text or embedding settings, does not require rebuilding the index.

If you change the materials' text or embedding settings, follow the [README instructions](../../README.md#lecture-05-retrieval): use `AIE_RAG_DB` to select an experimental database before building the index.

### How to Approach the Advanced Level

1. Choose a question you want the system to answer. First identify pages supporting the answer, such as an explanation spanning sections or a comparison of related terms
2. Design the retrieval method. Options include how Tree returns the table of contents and preview text; Graph relationship types, hop counts, and candidate selection; or combining retrieval methods
3. Explain your data structure, storage, and retrieval method, along with your reasons for choosing them
4. Compare with basic RAG using the same question, model, and target materials. Record answers, cited evidence, time, token counts, and estimated generation API cost
5. Give examples of improvements and failures, and discuss whether you would adopt the method for your use case

You may use AI tools. Describe what you ran and verified yourself. Follow the course announcements for the deadline.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `GEMINI_API_KEY` is missing | Did you register the Codespaces secret? If added after startup, did you restart Codespaces? |
| "Search database not found" | The localized materials, index, and runtime update are pending in this release. After that update is available, get it and check that `data/rag_data/index.sqlite3` exists. If `AIE_RAG_DB` is set, check that destination |
| API rate limit reached | Wait as directed by the message, then retry |
| The question is empty | If you opened another terminal, set `AIE_QUESTION` again |
| Search results do not answer the question | Try search alone with `app.retrieval` and check the search terms, target materials, and result count |
| Full context exceeds the input limit | Record the error and execution settings, then try another method. Mark any unrun entries accordingly |

Results can vary for the same question. Avoid judging an entire method from one success or failure; check which evidence was retrieved and used.
