# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：The three levels is represent 3 level of difficulty: basic - filling in code, implementation - independent coding and debugging, and advanced - combining multiple concepts. It acknowledged that it lacked the course-specific context and presented this as a general interpretation.
- 用語集の正しい意味と比べて気づいたこと：The glossary defines the levels as Basic (reviewing lecture content), Implementation (writing code yourself), and Advanced (research or experimentation). I noticed that a plausible general answer can still miss important course-specific rules, even when the model acknowledges uncertainty.
- 表示できたトークン数（入力 / 出力）：Input: 21 / Output: 546

## 宿題

- 取り組んだレベル：発展
- やったこと：I completed 3 levels. I run the 2 questions (3 times per each) each while changing the model (AIE_MODEL env var). Modify the codes which help me ask follow-up questions while keeping the conversation history. I added codes to measure response time and display input and output token counts, then I compared gemini-3.5-flash-lite and gemini-3.8-flash using two prompts: a one-sentence explanation of LoRA and an approximately 200-word explanation.
- 結果：in basic level, AI give me 3 different answer for each time I ask the same question. In implementation level, the model does not remember earlier chat before. after adding code in ask.py, the model can stored, remember and follow up the content and request in the chat and then summarized, Gemini 3.8 Flash produced more output tokens and had higher average response times for both prompts in this experiment. However, response times varied substantially. Repeated 503 errors usually appear with Gemini 3.8 Flash. The more input I give, the more time it responses, the correct level may be impacted too because the more detail I put, the clearer context AI understand.The more token means more cost and reach the limit sooner.
  Model | Prompt | Successful runs | Response time (s) | Input tokens | Output tokens
  gemini-3.5-flash-lite | Short | 3 | 31.643 | 8 | 37.00
  gemini-3.5-flash-lite | Long | 3 | 33.219 | 26 | 271.33
  gemini-3.8-flash | Short | 3 | 39.572 | 8 | 55.00
  gemini-3.8-flash | Long | 2 | 69.777 | 26 | 305.50
- 気づき・疑問：Longer prompts increased input tokens from 8 to 26 and produced substantially more output tokens. However, output length alone did not explain response time: some short answers took much longer than others. The measurements represent elapsed API-call time, rather than model computation alone.
I think that free-tier limits involve requests per minute, input tokens per minute, and requests per day, with limits depending on the model and project tier. Repeated experiments consume request allowance, while longer prompts and conversation histories increase input-token usage. The higher-tier model will use more tokens and usually appears with a 503 error.
