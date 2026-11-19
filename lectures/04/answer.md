# 第4回 解答

## 演習

- 基準別の一致率（直す前）：Grounding: 5/9; Scope: 7/10; Hint: 6/10; Clarity: 5/10; Lecture mark: 7/10.
- 要確認の件数（直す前）：1 item: grounding in case 05, concerning the explanation of RAG after acknowledging that it was absent from the glossary.
- 直した基準と、書き足した方針：I revised the grounding criterion by adding this policy:
“For a term absent from the glossary, stating its absence and then adding a general definition unsupported by the glossary is grounding=fail; stating its absence alone is pass.”
I also removed the corresponding unresolved-policy section.
- 基準別の一致率と要確認の件数（直した後）：Grounding: 5/9; Scope: 7/10; Hint: 6/10; Clarity: 5/10; Lecture mark: 7/10.
1 item required review: grounding in case 08. The review item therefore moved from case 05 to case 08.
- 講師のラベルと自分のラベルで判定が違った項目と、そう判定した理由：Some judge are different because I use translation, it make the question and answer has errors and I mark it as fail
- 気づき・疑問：Clarifying the rubric did not improve criterion-level agreement in this comparison. Case 05 changed from unsure to pass, although the added policy required fail for an unsupported general definition. The judge therefore did not apply the revised policy as intended.

## 宿題

- 取り組んだレベル：発展
- やったこと：I did 3 levels.
At level 1: I compare 2 judge runs, use the same 10 cases, saved human labels and model (gemini 3.5 flash lite, temperature 0). I clarified 1 grounding policy: stating that a term is absent from the glossary and then adding a general definition unsupported by the glossary should receive fail. Then I removed the corresponding unsolved policy section.
At level 2: I add new 10 questions and expected behavior. Then I generated the answers using agent in app/agent.py. Finally, I review, evaluate and label them as level 1. I saved it at  lectures/04/my_labels.jsonl.
At level 3: I selected SWE -bench verified, which contains 500 software engineering tasks drawn from real github issues. I tried my best to read their source and understand 3 example tasks. Then I investigate how the dataset was contructed, reviewed and graded comparing with level 1 and 2 that I did previously.
- 結果：
At level 1: I see the agreement remain unchange for each criteria. Grounding: 5 out of 10, scope: 7 out of 10, hint: 6 out of 10, clarity: 5 out of 10, lecture mark: 7 out of 10. Both runs had 90% coverage and 19 criterion-level disagreement. Overall agreement chaged from 9 out of 9 to 8 out of 9
At level 2: I use gemini 3.5 flash lite to evaluate, the agreement is 8 out of 10 for grounding (2 disagreement is in question 2 and 6) and 10 out of 10 for remaining criterions. Overall agreement is 9 out of 10 with 100% coverage, no unsure judgement.
At level 3: I understand the task astropy__astropy-12907 as A function produces an incorrect dependency matrix when models are nested inside other models. The task requires correcting this behavior. While the task astropy__astropy-13033 is Removing a required column from a time-series object produces a misleading error message. The program should clearly identify the missing required columns and the task astropy__astropy-13453 is When exporting a table to HTML, the program ignores the user’s requested number formatting. The output should respect that formatting. With my background, I can not independently implement these fixes. The tasks originated from existing open-source development work. Each verified process has 93 developers reviewed 1 699 rondomly selected SWE-bench samples. The reviewers assessed whether the problem description was sufficiently clear, whether the test could unfairly reject valid solutions.They are huge project comparing with assignment level 1 and 2. And use code to fix, not the judge or grade. They are so complex. 
- 気づき・疑問：Clarify the rubric do not produce the intended judgement in this run and the equal coverage did not mean that the same case were included. Human labels may been affected by interface redering errors. Code is suitable for explicit format checks but it rejects an English references. The criterion such as grounding, hint need to be describe clearcy, full context to help LLM understand the case, from that, it can suggest more accurate answer. At the end of level 3, I realize that LLM may interpret a requirement differently forn the person who create the task, especially when important expectations are unstated. Difficult can come from solving the problem and understand the evaluators consider acceptable. In fact, human verification also may not guarantee a flawless benchmark.