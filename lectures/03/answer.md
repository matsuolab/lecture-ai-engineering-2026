# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い： The difference is LLM in lec01 only give the general explanation of three levels and miss the course rule that completing any one level is enough. While LLM in lec03 look up for 3 levels found no match at the beginning, but the agents searched for levels, found relevant glossary entry explain the rule accurately.
- `--trace` で見えたツール呼び出し（ツール名と引数）：the agent called search_glossary separately with query ='LoRA' and query='QLoRA'.
- 1つの質問での LLM 呼び出し回数（`requests`）：The trace showed 2 model requests and 2 tool calls
- 追加したツールと、docstring に書いた説明：I add make_quiz (lecture:int) to select glossary term from requested lectures and return question + definition. Docstring tells the agent to use it when learner ask for a quiz or review question in particular lecture. I set up make_quiz with lecture=2, the tool returns question and answer about quantization.

## 宿題

- 取り組んだレベル：発展
- やったこと： I did all 3 levels.
In basic level, I changed one instruction into "the agent could answer familiar AI questions directly and use the glossary for course specific terms or when unsure and I ran the same LoRA and QLoRA question before and after the change. I use gemini 3.5 flash lite model.
In implementation level, I added save_learning_log and required confirmation before it could write the answer. I test both scenarios: yes and no.
In advanced level, I select part a. I configured an ADK agent with same model settings, instructions, 3 tools.Pydantic AI version register tools individually with agent.tool_plain. the ADK version pass the functions in the tools list when creating root_agent. I test 3 same prompts in separate ADK sessions
- 結果：
In basic level, Both run searched for LoRA and QLoRA separately, same order, 2 model requests and 2 tool calls. Input token changed from 1350 to 1362 and output tokens changed from 232 to 188 -> reduce memory use
In implementation level, the result is successful, when I approved, the tool reported the part of new file in learning_log. When I refused, at the first time, the trace showed 2 denied calls and the model claimed it had saved the note. I fixed it and run again, the result is it printed Learning log was not saved.
In advanced level, for first question, Pydantic AI found the entry and explained the one-level rule in English while ADK answer in Japanese that it could not find the term. For second question, 2 versions explained the main difference between LoRA and QLoRA and pointed to lecture. For the quiz, both produced lec02 review question: Pydantic AI ask about quantization and ADK asked about fine-tunning
- 気づき・疑問：Making glossary use optional do not change tool calls, the following answer may shorter and spend less token but need to run more to verify this. Blocking writing and reporting the answer are separate responsibilities. The approved step blocked the write but the model still described it incorrectly, having CLI report the refusal directly fixed the mismatch. Finally, The glossary showed that the same model setting and tools can still response different answers, ADK terminal output do not show the search query => can not identify the cause the difference to the framework and the different quiz topics are consistent with the tool choosing a term at random.
