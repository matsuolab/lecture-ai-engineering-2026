# 第5回 解答

## 演習

- 回答モデル（実行時の`[model]`）：gemini-3.5-flash-lite
- 比較した質問：question 1: In Lecture 2, what does LoRA freeze and what does it train? What does QLoRA add?.
- 対象資料（全文投入と他の方式で範囲が違う点も記録）：Full-context mode receive all 9 documents (438 pages). Vector, Tree, and Graph use the main lecture materials for Lectures 1–3 (214 pages). Question referred to Lecture 2.

### 各方式の結果

| 方式 | 回答の要点・正しさ | 引用ページと根拠 | 時間（秒） | 入力／出力トークン数 | モデル応答回数 | 生成API推定費用（USD） |
|---|---|---|---|---|---|---|
| 全文投入 |Correct: LoRA freezes the original weights and trains small adapter matrices. QLoRA adds 4-bit quantization of the original weights|Lecture 2, p.52 for freezing and training; pp.51–52 for quantization.|3.04|117,023/172|1|0.035537|
| ベクトル検索 |Correct on all three points. The search returned p.52 as its first result|Lecture 2, pp.51–52. Page 52 identifies the fixed weights W and the trainable matrices A and B.|2.25|3,025/209|2|0.001430 |
| Tree |Correct on all three points. The agent opened both relevant pages before answering|Lecture 2, pp.51–52. Page 51 compares LoRA and QLoRA; p.52 explains which weights are frozen, trained, or quantized|9.94|13,694/357|6|0.005001|
| Graph |Correct: W stays fixed, A and B are trained, and QLoRA quantizes the original weights to 4 bits|Lecture 2, p.52 for LoRA and pp.51–52 for QLoRA. The trace showed p.52 as a starting page for the graph search|3.96|5,443/187|2|0.002100|

<!-- 未実行・算定不可の場合は、その旨を書いてください。質問を追加した場合は、質問ごとに表を分けてください。 -->

- 検索だけを実行して見つかったページと、その本文で確認できたこと：I ran uv run python -m app.retrieval "LoRA QLoRA difference code". 5 results were Lecture 2 PDF pages 52, 51, 60, 47, and 61, in that order. Page 52 directly answered. W stays fixed, only A and B are trained, and QLoRA stores the original weights in 4-bit form. It gave the example of about 4 GB for a 7B model’s weights.
- `--trace`で見えたツール呼び出し（ツール名・引数・回数、Treeでたどった目次など）： Full-context mode make with no retrieval tool calls. Vector search called search_materials once with the query LoRA freeze train QLoRA add. Tree called browse_tree five times: root -> lec02-main -> lec02-main-s045 -> lec02-main-p051 -> lec02-main-p052. Graph called search_graph once with the query LoRA freeze train QLoRA add. Its visible output show lec02-main-p052 as a starting page; the rest of the tool output are truncated.
- 取得した情報が足りなかった例、取得できたのに回答へ使えなかった例：Sometimes, the first result, p.52, supported the 4 GB answer but did not explain virtual tokens. The agent needed another search to find that evidence on p.51. It then reported that it could not find the information. The trace shows that the relevant page titles and previews were available but it does not show that the agent read and ignored their full text.
- 今回の用途に採用したい方式と、その理由・比較条件の限界：I think I can use Vector search for factual questions which require a PDF page citation. All four methods answered correctly, but Vector needed only one search, took 2.25 seconds, and had the lowest estimated generation cost (USD 0.001430). I also think not generalize the timing results to other questions.
- 気づき・疑問：I learned to check which page supports each part of an answer. I want to test more questions whose answers span two pages and measure how often each method finds.

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：発展
- やったこと（変更したファイル・設定・処理、または設計した取得方法）：I completed 3 level one by one to understand deeply each level.
In basic, I set up as guidance requested. Then change RAG_TOP_K from 5 to 1. This limited each RAG search to one page instead of 5. 
In implementation, I modified app/retrieval.py so that the setting AIE_RAG_NEIGHBORS=1 return the best matching page plus previous and next page from the same document. I also add the code to avoid duplication and keep RAG_TOP_K 1
In advanced, I change the page preview in browse_tree in app/retrieval.py to skip blanks line and repeated headings, show upto 120 characters in the first line to check whether it saves cost and time responses.
- 比較した質問と、固定した条件（モデル・対象資料など）：
In basic, the question is In Lecture 2, what does LoRA freeze and what does it train? What does QLoRA add?. The model: gemini-3.5-flash-lite. I use the same search index lecture 1- 3, RAG command. I only change RAG_TOP_K
In implementation, keep the question in basic level and add 1 more question: what prefix/prompt tuning adds to the input and how much memory stores the 4-bit weights of a 7B model. The evidence is on page 51 and 52. I use gemini-3.5-flash-lite as basic level, same lecture index and materials. I compared normal search and adjacent-page retrieval using trace. 
In advanced, I keep the same settings as level 1 and 2. Using gemini-3.5-flash-lite, 2 questions, same lecture materials. Then compare basic vector search (RAG_TOP_K = 1, without neighboring pages), the original Tree, and the modified Tree.
- 結果（変更前後の回答・根拠、`--trace`の出力、時間・トークン数・生成API推定費用など）：
In basic:
Measurement|RAG_TOP_K = 5|RAG_TOP_K = 1
Time|2.25 s|2.85 s
Input tokens|3,025|1,187
Output tokens|209|231
Estimated generation API cost|$0.001430|$0.000934
-> In both run, one call to search_materials with the query LoRA freeze train QLoRA add, lec02-main-p052 is the first result. With 5 pages, the answer is more qualified answer in page 51 and 52. But with 1 page, the answer still correct and cost less.

In implementation:
Question|Retrieval|Search calls|Input / output tokens|Time|Est. generation cost
Q1: LoRA/QLoRA|Normal|1|1,187 / 231|2.85 s|$0.000934
Q1: LoRA/QLoRA|With adjacent pages|1|2,092 / 181|3.03 s|$0.001080
Q2: Prompt tuning and 7B weights|Normal|3|4,361 / 177|30.96 s|$0.001751
Q2: Prompt tuning and 7B weights|With adjacent pages|1|2,158 / 143|2.29 s|$0.001005
-> Both method can show LoRA freezes the original weights and trains matrices A and B while QLoRA add 4-bit quantization. Normal search cited page 52 throughout, adjecent page cited 51 for quantization at Q1. For Q2, both methods cited 51 for trainable virtual tokens and page 52 for approximately 4 GB of weight storage.

In advanced,
Question|Method|Answer and PDF evidence|Tool calls|Input / output tokens|Time|Est. generation cost (USD)
Q1|Basic|Correct; p.52|1|1,187 / 231|2.85 s|0.000934
Q1|Original Tree|Correct; pp.51–52|5|13,694 / 357|6.94 s|0.005001
Q1|Modified Tree|Correct; p.52	|4|9,314 / 347|22.02 s|0.003662
Q2|Basic|Both parts correct; pp.51 and 52|3|4,361 / 177|30.96 s|0.001751
Q2|Original Tree|Both parts correct; pp.51 and 52|6|19,875 / 258|8.45 s|0.005522
Q2|Modified Tree|Neither part answered; no citation|10|57,629 / 328|28.49 s|0.010475
-> For Q1, the modified Tree followed root -> lec02-main -> lec02-main-s045 -> lec02-main-p052. Page 52 alone support all claims: LoRA freeze the original weights, trains the small low-rank matrices A, B, QLoRA adds 4-bit quantization of the original weights. For Q2, Basic and the original Tree identified learnable virtual tokens in page 51); approximately 4 GB to store the 7B model’s 4-bit weights in page 52. The modified Tree listed 2 pages under s045 but opened neither the appendix and other lectures, and reported it could not find the information.

- 改善した例と、残る失敗・制約：
In basic, use less page make less cost while the answer still correct. the response time is not changed significantly but it is happened. But with the more complicated question. it may need more cost the make sure the answer is qualified.
In implementation, Q2 showed the clearest improvement. Normal search returned page 52, 46,51 in separate calls, while in adjecent page retrieval, the model use page 51, 52 the answer after one call. For Q1, the extra context increase input tokens and cost without improving answer -> they may improve the time response.
In advanced, Q1 show the modified tree open only page 52, not page 51. It preserve the correct answer, reduce token from 13,694 to 9,314 although time the increase from 6.94 to 22.02 s. Q2 contain the specific detail requested virtual tokens or about 4 GB. The relevant page are visible but the model moved on without reading them.
- 気づき・疑問：I understand the result was checking myself and can point to the evidence for each part of the answer and how many page need for answering. Moreover, I guess that sending more pages may use more tokens but the Q2 showed why that is not always true. I need to test more whether the system can decide when it need a neighboring page. Lastly, I know hơ to distinguish between a page appearing in the table of content and the agent actually reading it. It is only 1 experiment, I need to test and record the result more before making decision, but it is the foundation for me in fuether study.
