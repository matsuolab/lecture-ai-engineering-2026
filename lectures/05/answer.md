# Lecture 5 Answers

## Exercise

- Answering model (`[model]` at runtime): `gemini-3.5-flash-lite`
- Question compared: `"In Lecture 2, what does LORA freeze and what does it train? What does QLORA add?"`
- Target materials (note the scope difference between full text and other methods):
  - **Full text (`--full-context`):** All 9 documents / 438 pages (228,008 input characters) passed at once[cite: 14].
  - **Vector search / Tree / Graph:** Main lecture materials for Lectures 1–3 (`lec01-main`, `lec02-main`, `lec03-main`, 214 pages total)[cite: 14].

### Results by Method

| Method | Key Answer Points & Correctness | Cited Pages & Evidence | Time (s) | Input / Output Tokens | Model Responses | Est. Gen. API Cost (USD) |
|---|---|---|---|---|---|---|
| Full text | Correct. Accurately stated that LoRA freezes foundation model weights and trains only small added matrices, while QLoRA additionally compresses original weights to 4-bit. | Lecture 2, PDF p.51, p.52 (p.52 describes freezing original weights $W$, training low-rank matrices $A, B$, and 4-bit compression)[cite: 15, 20]. | 2.62 | 117,023 / 84 | 1 | $0.035317 |
| Vector search | Correct. Accurately explained that LoRA freezes original weights and trains only low-rank matrices $A, B$, while QLoRA adds 4-bit quantization of original weights. | Lecture 2, PDF p.51, p.52 (p.51 covers PEFT overview; p.52 details LoRA/QLoRA)[cite: 15, 20]. | 2.06 | 3,112 / 226 | 2 | $0.001499 |
| Tree | Correct. Navigated the TOC hierarchy and accurately identified what LoRA freezes/trains and what QLoRA adds for memory efficiency. | Lecture 2, PDF p.52 (fetched 717 chars of body text from `lec02-main-p052`). | 3.74 | 9,204 / 290 | 5 | $0.003486 |
| Graph | Correct. Accurately covered LoRA's frozen/trained parameters and QLoRA's 4-bit weight compression. | Lecture 2, PDF p.51, p.52 (seeded on `lec02-main-p052` and expanded surrounding/related pages). | 2.08 | 5,769 / 212 | 2 | $0.002261 |

- Pages found by running retrieval alone and what was verified in their body text:
  - Running `uv run python -m app.retrieval "LoRA QLORA difference"` returned the top 5 results from Lecture 2: **p.52** (LoRA & QLoRA), **p.51** (PEFT), **p.60** (Today's Exercise: QLoRA), **p.47** (Evidence & Theories), and **p.61** (Exercise Flow).
  - The body text of **p.52** directly confirmed all required evidence: original weights $W$ are frozen and not trained, only small low-rank matrices $A$ and $B$ are trained, and QLoRA compresses original weights to 4-bit (roughly 1/4 size)[cite: 15, 20].
- Tool calls visible in `--trace` (tool names, arguments, call counts, TOC path traversed in Tree):
  - **Full text:** No tool calls (completed in 1 model response).
  - **Vector search:** Called `search_materials({'query': 'LORA freeze train QLORA'})` once (2 model responses).
  - **Tree:** Called `browse_tree` 4 times (5 model responses), traversing `browse_tree({})` (course list) → `browse_tree({'node_id': 'lec02-main'})` (Lecture 2 TOC) → `browse_tree({'node_id': 'lec02-main-s045'})` (section "When and how to fix the chosen model") → `browse_tree({'node_id': 'lec02-main-p052'})` (fetched full text of PDF p.52)[cite: 16, 23, 25].
  - **Graph:** Called `search_graph({'query': 'LoRA freeze train QLoRA'})` once (2 model responses), expanding from seed `lec02-main-p052` via adjacent pages and shared terms[cite: 26, 27].
- Examples where retrieved info was insufficient, or retrieved but unused in the final answer:
  - For this single-page question, all necessary evidence was present on p.52, so there was no missing evidence[cite: 22]. However, vector search also retrieved p.60–61 (exercise instructions) and p.47 (RAG vs. FT comparison), which were irrelevant to the prompt and remained unused in the final answer.
- Method to adopt for this use case, rationale, and limitations of the comparison conditions:
  - **Method to adopt:** **Vector search (RAG)** for focused single- or few-page questions, and **Graph** for multi-page or cross-concept questions. Vector search achieved full accuracy at ~1/23 the cost ($0.001499 vs. $0.035317) and faster latency (2.06 s vs. 2.62 s) compared to full text.
  - **Comparison limitations:** Full text covered all 9 documents (438 pages) whereas the three search modes were scoped to Lectures 1–3 (214 pages)[cite: 14, 38]; additionally, metrics reflect single runs and can fluctuate with API/network latency[cite: 38].
- Insights & questions:
  - Passing all materials into context does not guarantee better answers and dramatically inflates input tokens (117,023 tokens) and cost[cite: 13, 72]. Selective retrieval provides major cost and efficiency gains[cite: 95].
  - Tree search can locate the exact supporting slide (p.52) purely through TOC hierarchy without a vector DB[cite: 24, 32], though multi-step navigation increases model calls (5) and latency (3.74 s).

## Homework

- Level attempted: Basic, Implementation, and Advanced (all three tiers completed)[cite: 33]
- What I did (modified files, settings, processing, or custom retrieval design):
  1. **Basic (`app/config.py`):** Reduced `RAG_TOP_K` from the default `5` to `2` to measure the effect of retrieving fewer chunks[cite: 31, 34].
  2. **Implementation (`app/retrieval.py`):** Extended `search()` so each retrieved hit also fetches **1 page before (`page - 1`) and 1 page after (`page + 1`)** within the same `document_id` (keyed by `(document_id, page)` to prevent cross-document leaks) and deduplicated results by `page_id`[cite: 31, 34].
  3. **Advanced (`app/retrieval.py`):** Enhanced `search_graph()` to (a) filter out overly generic high-degree hub terms (`max_term_degree = 12`) during 2-hop expansion to reduce noise, and (b) apply a multi-seed overlap bonus (`multi_seed_bonus`) so pages reachable from multiple seed hits rank higher within `GRAPH_MAX_RESULTS`[cite: 35].
- Questions compared and fixed conditions (model, target materials, etc.):
  - **Fixed conditions:** Model `gemini-3.5-flash-lite`; search scope `lec01-main`, `lec02-main`, `lec03-main` (214 pages)[cite: 14, 34, 35].
  - **Question 1 (Basic & Implementation):** `"In Lecture 2, what does LORA freeze and what does it train? What does QLORA add?"` (evidence: Lecture 2, PDF p.52)[cite: 29].
  - **Question 2 (Advanced — multi-page comparison):** `"In Lecture 3, what is the difference between compaction and cross-session memory, and do all daily notes become long-term memory?"` (evidence: Lecture 3, PDF p.13, p.39, p.40)[cite: 29].
  - **Question 3 (Advanced — out-of-materials check):** `"What is our RAG system's measured average response time and accuracy today?"` (not present in lecture materials)[cite: 29].
- Results (before/after answers & evidence, `--trace` outputs, time, token counts, estimated generation API cost):
  - **1. Basic (`RAG_TOP_K: 5 → 2`, Question 1):**
    - Before: 2.06 s | 3,112 in / 226 out tokens | 2 responses | $0.001499 (cited Lecture 2, PDF p.51, p.52).
    - After: 1.93 s | 1,737 in / 204 out tokens | 2 responses | $0.001031 (cited Lecture 2, PDF p.51, p.52).
    - Tool call: `search_materials({'query': 'LORA freeze train QLORA add'})` once. Preserved accuracy while cutting input tokens by ~44% and cost by ~31%.
  - **2. Implementation (±1 adjacent page + deduplication, `RAG_TOP_K = 5`, Question 1):**
    - Standalone `app.retrieval` expanded 5 hits into 11 unique pages (p.51, 52, 53, 50, 59, 60, 61, 46, 47, 48, 62) with zero duplicates or cross-document leaks[cite: 34].
    - Before (normal search): 2.06 s | 3,112 in / 226 out tokens | 2 responses | $0.001499.
    - After (±1 adjacent page): 2.29 s | 5,264 in / 324 out tokens | 2 responses | $0.002389 (cited Lecture 2, PDF p.51, p.52; also incorporated detail that trained parameters can be <1% of total).
  - **3. Advanced (Improved `search_graph`, Questions 2 & 3):**
    - Question 2 (Multi-page comparison):
      - Basic RAG baseline: 3.79 s | 6,627 in / 510 out tokens | 3 responses (2 `search_materials` calls) | $0.003263 (cited Lecture 3, PDF p.13, p.39, p.40).
      - Default Graph baseline: 2.98 s | 5,394 in / 407 out tokens | 2 responses (1 `search_graph` call) | $0.002636 (cited Lecture 3, PDF p.39, p.40).
      - Improved Graph: 7.63 s | 5,416 in / 522 out tokens | 2 responses (1 `search_graph` call, seeded on `lec03-main-p038`) | $0.002930 (cited Lecture 3, PDF p.38, p.39, p.40, p.65).
    - Question 3 (Out-of-materials question):
      - Improved Graph: 1.85 s | 5,328 in / 146 out tokens | 2 responses (1 `search_graph` call, seeded on `lec02-main-p013`) | $0.001963. Properly stated that current system metrics are not in the materials and cited Lecture 2, PDF p.13 on repeated evaluation.
- Improved examples and remaining failures / constraints:
  - Improvements:
    - In Basic, lowering `RAG_TOP_K` to `2` cut token usage and cost substantially on a single-slide question without losing precision[cite: 34].
    - In Implementation, adjacent-page retrieval automatically pulled surrounding context such as p.53 (practical FT vs. RAG decision boundary) and p.50 (step-by-step decision order)[cite: 34].
    - In Advanced, whereas Basic RAG needed two separate search tool calls (3 model turns) for Question 2, Improved Graph resolved it in a single `search_graph` call with cohesive context across p.38–40 (external memory persistence and `MEMORY.md` filtering), and cleanly abstained on the unanswerable Question 3 without hallucinating[cite: 22, 35].
  - **Remaining failures & constraints:**
    - In Implementation, expanding ±1 page increased input tokens by ~69% and generation cost by ~59%, introducing tangential pages (such as p.62 next-lecture preview) when the core answer was already on a single slide[cite: 22, 34].
    - In Advanced, response latency reached 7.63 s on the multi-page graph query, and citation strings (e.g., p.65) still require manual verification against slide text to ensure every cited page directly supports the claim[cite: 11, 22, 35].
- Insights & questions:
  - Expanding retrieved context (via adjacent pages or graph traversal) reduces the risk of missing multi-slide evidence, but introduces a clear trade-off with noise, token cost, and latency[cite: 34, 55, 72]. Dynamically adapting `top_k` or graph expansion based on whether a query is single-fact or multi-hop is a promising next step.